"""
Tests for self assessment handlers in Open Assessment XBlock.
"""


import copy
import datetime
import json

from unittest import mock
import pytz

from ieia.assessment.api import self as self_api
from ieia.workflow import api as workflow_api
from ieia.xblock.utils.data_conversion import create_rubric_dict

from .base import SubmissionTestMixin, XBlockHandlerTestCase, scenario


class TestSelfAssessment(XBlockHandlerTestCase, SubmissionTestMixin):
    """
    Tests for the self-assessment XBlock handler.
    """

    maxDiff = None

    SUBMISSION = ('ՇﻉรՇ', 'รપ๒๓ٱรรٱѻก')

    ASSESSMENT = {
        'options_selected': {'𝓒𝓸𝓷𝓬𝓲𝓼𝓮': 'ﻉซƈﻉɭɭﻉกՇ', 'Form': 'Fair'},
        'criterion_feedback': {},
        'overall_feedback': ""
    }

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_handler(self, xblock):
        # Create a submission for the student
        submission = self.create_test_submission(xblock)

        # Submit a self-assessment
        resp = self.request(xblock, 'self_assess', json.dumps(self.ASSESSMENT), response_format='json')
        self.assertTrue(resp['success'])

        # Expect that a self-assessment was created
        assessment = self_api.get_assessment(submission["uuid"])
        self.assertEqual(assessment['submission_uuid'], submission['uuid'])
        self.assertEqual(assessment['points_earned'], 5)
        self.assertEqual(assessment['points_possible'], 6)
        self.assertEqual(assessment['scorer_id'], 'Bob')
        self.assertEqual(assessment['score_type'], 'SE')
        self.assertEqual(assessment['feedback'], '')

        self.assert_assessment_event_published(xblock, 'openassessmentblock.self_assess', assessment)

        parts = assessment['parts']
        parts.sort(key=lambda x: x['option']['name'])
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]['option']['criterion']['name'], 'Form')
        self.assertEqual(parts[0]['option']['name'], 'Fair')
        self.assertEqual(parts[1]['option']['criterion']['name'], '𝓒𝓸𝓷𝓬𝓲𝓼𝓮')
        self.assertEqual(parts[1]['option']['name'], 'ﻉซƈﻉɭɭﻉกՇ')

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_no_submission(self, xblock):
        # Submit a self-assessment without first creating a submission
        resp = self.request(xblock, 'self_assess', json.dumps(self.ASSESSMENT), response_format='json')
        self.assertFalse(resp['success'])
        self.assertGreater(len(resp['msg']), 0)

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_updates_workflow(self, xblock):

        # Create a submission for the student
        submission = self.create_test_submission(xblock)

        with mock.patch('ieia.xblock.workflow_mixin.workflow_api') as mock_api:

            # Submit a self-assessment
            resp = self.request(xblock, 'self_assess', json.dumps(self.ASSESSMENT), response_format='json')

            # Verify that the workflow is updated when we submit a self-assessment
            self.assertTrue(resp['success'])
            expected_reqs = {
                "peer": {"must_grade": 5, "must_be_graded_by": 3, "enable_flexible_grading": False}
            }
            mock_api.update_from_assessments.assert_called_once_with(submission['uuid'], expected_reqs, {})

    @scenario('data/feedback_only_criterion_self.xml', user_id='Bob')
    def test_self_assess_feedback_only_criterion(self, xblock):
        # Create a submission for the student
        submission = self.create_test_submission(xblock)

        # Submit a self assessment for a rubric with a feedback-only criterion
        assessment_dict = {
            'options_selected': {'vocabulary': 'good'},
            'criterion_feedback': {
                'vocabulary': 'Awesome job!',
                '𝖋𝖊𝖊𝖉𝖇𝖆𝖈𝖐 𝖔𝖓𝖑𝖞': 'fairly illegible.'
            },
            'overall_feedback': ''
        }
        resp = self.request(xblock, 'self_assess', json.dumps(assessment_dict), response_format='json')
        self.assertTrue(resp['success'])
        assessment = self_api.get_assessment(submission["uuid"])

        # Check the assessment for the criterion that has options
        self.assertEqual(assessment['parts'][0]['criterion']['name'], 'vocabulary')
        self.assertEqual(assessment['parts'][0]['option']['name'], 'good')
        self.assertEqual(assessment['parts'][0]['option']['points'], 1)

        # Check the feedback-only criterion score/feedback
        self.assertEqual(assessment['parts'][1]['criterion']['name'], '𝖋𝖊𝖊𝖉𝖇𝖆𝖈𝖐 𝖔𝖓𝖑𝖞')
        self.assertIs(assessment['parts'][1]['option'], None)
        self.assertEqual(assessment['parts'][1]['feedback'], 'fairly illegible.')

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_workflow_error(self, xblock):
        # Create a submission for the student
        self.create_test_submission(xblock)

        with mock.patch('ieia.xblock.workflow_mixin.workflow_api') as mock_api:

            # Simulate a workflow error
            mock_api.update_from_assessments.side_effect = workflow_api.AssessmentWorkflowInternalError

            # Submit a self-assessment
            resp = self.request(xblock, 'self_assess', json.dumps(self.ASSESSMENT), response_format='json')

            # Verify that the we get an error response
            self.assertFalse(resp['success'])

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_handler_missing_keys(self, xblock):
        # Missing options_selected
        assessment = copy.deepcopy(self.ASSESSMENT)
        del assessment['options_selected']
        resp = self.request(xblock, 'self_assess', json.dumps(assessment), response_format='json')
        self.assertFalse(resp['success'])
        self.assertIn('options', resp['msg'])

    @scenario('data/self_assessment_scenario.xml', user_id='Bob')
    def test_self_assess_api_error(self, xblock):
        # Create a submission for the student
        self.create_test_submission(xblock)

        # Submit a self-assessment
        # Simulate an error and expect a failure response
        with mock.patch('ieia.xblock.apis.assessments.self_assessment_api.self_api') as mock_api:
            mock_api.create_assessment.side_effect = self_api.SelfAssessmentRequestError
            resp = self.request(xblock, 'self_assess', json.dumps(self.ASSESSMENT), response_format='json')

        self.assertFalse(resp['success'])


class TestSelfAssessmentRender(XBlockHandlerTestCase, SubmissionTestMixin):
    """
    Test rendering of the self-assessment step.
    The basic strategy is to verify that we're providing the right
    template and context for each possible state,
    plus an integration test to verify that the context
    is being rendered correctly.
    """

    @scenario('data/self_assessment_unavailable.xml', user_id='Bob')
    def test_unavailable(self, xblock):
        # Start date is in the future for this scenario
        self._assert_path_and_context(
            xblock,
            'legacy/self/oa_self_unavailable.html',
            {
                'self_start': datetime.datetime(5999, 1, 1).replace(tzinfo=pytz.utc),
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            }
        )

    @scenario('data/self_assessment_closed.xml', user_id='Bob')
    def test_closed(self, xblock):
        # Due date is in the past for this scenario
        self._assert_path_and_context(
            xblock,
            'legacy/self/oa_self_closed.html',
            {
                'self_due': datetime.datetime(2000, 1, 1).replace(tzinfo=pytz.utc),
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            }
        )

    @scenario('data/self_assessment_open.xml', user_id='Bob')
    def test_open_no_submission(self, xblock):
        # Without making a submission, this step should be unavailable
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_unavailable.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            }
        )

    @scenario('data/self_assessment_open.xml', user_id='James Brown')
    def test_open_in_peer_step(self, xblock):
        # Make a submission, so we're in the peer-assessment step
        self.create_test_submission(xblock)

        # Should still be able to access self-assessment because peer status can be skipped
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_assessment.html', {
                'file_upload_type': True,
                'self_submission': True,
                'prompts_type': True,
                'self_file_urls': True,
                'rubric_criteria': True,
                'user_language': True,
                'allow_latex': True,
                'user_timezone': True,
                'allow_multiple_files': True,
                'show_survey': False
            }
        )

    @scenario('data/self_assessment_open.xml', user_id='James Brown')
    def test_open_in_waiting_for_peer_step(self, xblock):
        # In the peer-->self configuration, if we're done with the
        # self step, but not with the peer step (because we're waiting
        # to be assessed), then the self step should display as completed.
        self.create_test_submission(xblock)
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_complete.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': None,
                'user_language': None,
                'show_survey': False
            },
            workflow_status='waiting',
            status_details={
                'self': {'complete': True},
                'peer': {'complete': False}
            }
        )

    @scenario('data/self_then_peer.xml', user_id="The Bee Gees")
    def test_self_then_peer(self, xblock):
        self.create_test_submission(xblock)

        # In the self --> peer configuration, self can be complete
        # if our status is "peer"
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_complete.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': None,
                'user_language': None,
                'show_survey': False
            },
            workflow_status="peer",
            status_details={
                'self': {'complete': True},
                'peer': {'complete': False}
            }
        )

    @scenario('data/self_assessment_open.xml', user_id='James Brown')
    def test_open_done_status(self, xblock):
        # Simulate the workflow status being "done"
        self.create_test_submission(xblock)
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_complete.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': None,
                'user_language': None,
                'show_survey': False
            },
            workflow_status='done'
        )

    @scenario('data/self_assessment_open.xml', user_id='James Brown')
    def test_open_cancelled_status(self, xblock):
        # Simulate the workflow status being "done"
        self.create_test_submission(xblock)
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_cancelled.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            },
            workflow_status='cancelled'
        )

    @scenario('data/self_assessment_open.xml', user_id='James Brown')
    def test_open_self_assessing(self, xblock):
        # Simulate the workflow being in the self assessment step
        submission = self.create_test_submission(xblock)
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_assessment.html',
            {
                'rubric_criteria': xblock.rubric_criteria,
                'self_submission': submission,
                'file_upload_type': None,
                'self_file_urls': [],
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            },
            workflow_status='self',
            submission_uuid=submission['uuid']
        )

    @scenario('data/self_assessment_open.xml', user_id='Bob')
    def test_open_completed_self_assessment(self, xblock):
        # Simulate the workflow being in the self assessment step
        # and we've created a self-assessment
        submission = self.create_test_submission(xblock)

        self_api.create_assessment(
            submission['uuid'],
            xblock.get_student_item_dict()['student_id'],
            {'𝓒𝓸𝓷𝓬𝓲𝓼𝓮': 'ﻉซƈﻉɭɭﻉกՇ', 'Form': 'Fair'},
            {}, "Good job!",
            create_rubric_dict(xblock.prompts, xblock.rubric_criteria)
        )
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_complete.html',
            {
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            },
            workflow_status='self',
            submission_uuid=submission['uuid']
        )

    @scenario('data/self_assessment_closed.xml', user_id='Bob')
    def test_started_and_past_due(self, xblock):
        # Simulate the workflow being in the self assessment step
        # Since we're past the due date, the step should appear closed.
        submission = self.create_test_submission(xblock)
        self._assert_path_and_context(
            xblock,
            'legacy/self/oa_self_closed.html',
            {
                'self_due': datetime.datetime(2000, 1, 1).replace(tzinfo=pytz.utc),
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            },
            workflow_status='self',
            submission_uuid=submission['uuid']
        )

    @scenario('data/self_assessment_closed.xml', user_id='Bob')
    def test_completed_and_past_due(self, xblock):
        # Simulate having completed self assessment
        # Even though the problem is closed, we should still see
        # that we completed the step.
        submission = self.create_test_submission(xblock)

        self_api.create_assessment(
            submission['uuid'],
            xblock.get_student_item_dict()['student_id'],
            {'𝓒𝓸𝓷𝓬𝓲𝓼𝓮': 'ﻉซƈﻉɭɭﻉกՇ', 'Form': 'Fair'},
            {}, "Good job!",
            create_rubric_dict(xblock.prompts, xblock.rubric_criteria)
        )

        # This case probably isn't possible, because presumably when we create
        # the self-assessment, the workflow status will be "waiting" or "done".
        # We're checking it anyway to be overly defensive: if the user has made a self-assessment,
        # we ALWAYS show complete, even if the workflow tells us we're still have status 'self'.
        self._assert_path_and_context(
            xblock, 'legacy/self/oa_self_complete.html',
            {
                'self_due': datetime.datetime(2000, 1, 1).replace(tzinfo=pytz.utc),
                'allow_multiple_files': True,
                'allow_latex': False,
                'prompts_type': 'text',
                'user_timezone': pytz.utc,
                'user_language': 'en',
                'show_survey': False
            },
            workflow_status='self',
            submission_uuid=submission['uuid']
        )

    @scenario('data/self_assessment_open.xml', user_id='Bob')
    def test_integration(self, xblock):
        # Simulate the workflow being in the self assessment step
        # and we've created a self-assessment
        submission = self.create_test_submission(xblock, submission_text=("Test submission 1", "Test submission 2"))

        xblock.get_workflow_info = mock.Mock(return_value={
            'status': 'self', 'submission_uuid': submission['uuid']
        })

        resp = self.request(xblock, 'render_self_assessment', json.dumps({}))
        self.assertIn('in progress', resp.decode('utf-8').lower())
        self.assertIn('Test submission', resp.decode('utf-8'))

    @scenario('data/self_assessment_open.xml', user_id='Bob')
    def test_retrieve_api_error(self, xblock):
        # Simulate the workflow being in the self assessment step
        xblock.get_workflow_info = mock.Mock(return_value={'status': 'self'})

        # Simulate an error from the submission API
        with mock.patch('ieia.xblock.apis.assessments.self_assessment_api.self_api') as mock_api:

            mock_api.get_assessment.side_effect = self_api.SelfAssessmentRequestError
            resp = self.request(xblock, 'render_self_assessment', json.dumps({}))
            self.assertIn('error', resp.decode('utf-8').lower())

    def _assert_path_and_context(
            self, xblock, expected_path, expected_context,
            workflow_status=None, status_details=None,
            submission_uuid=None
    ):
        """
        Render the self assessment step and verify:
            1) that the correct template and context were used
            2) that the rendering occurred without an error

        Args:
            xblock (OpenAssessmentBlock): The XBlock under test.
            expected_path (str): The expected template path.
            expected_context (dict): The expected template context.

        Keyword Arguments:
            workflow_status (str): If provided, simulate this status from the workflow API.
            workflow_status (str): If provided, simulate these details from the workflow API.
            submission_uuid (str): If provided, simulate this submision UUI for the current workflow.
        """
        if workflow_status is not None:
            # Assume a peer-->self flow by default
            if status_details is None:
                status_details = {
                    'peer': {'complete': workflow_status == 'done'},
                    'self': {'complete': workflow_status in ['waiting', 'done']}
                }
            xblock.get_workflow_info = mock.Mock(return_value={
                'status': workflow_status,
                'status_details': status_details,
                'submission_uuid': submission_uuid
            })
        path, context = xblock.self_path_and_context()

        expected_context['xblock_id'] = xblock.scope_ids.usage_id

        self.assertEqual(path, expected_path)
        self.assertCountEqual(context, expected_context)

        # Verify that we render without error
        resp = self.request(xblock, 'render_self_assessment', json.dumps({}))
        self.assertGreater(len(resp), 0)
