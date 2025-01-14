"""
Tests for the assessment Django models.
"""


import copy

import ddt

from submissions.api import create_submission
from ieia.assessment.api.self import create_assessment
from ieia.assessment.errors import SelfAssessmentRequestError
from ieia.assessment.models import Assessment, AssessmentPart, InvalidRubricSelection
from ieia.assessment.serializers import rubric_from_dict
from ieia.test_utils import CacheResetTest

from .constants import RUBRIC


@ddt.ddt
class AssessmentTest(CacheResetTest):
    """
    Tests for the `Assessment` and `AssessmentPart` models.
    """

    def test_create_with_feedback_only_criterion(self):
        rubric = self._rubric_with_one_feedback_only_criterion()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Create assessment parts
        # We can't select an option for the last criterion, but we do
        # provide written feedback.
        selected = {
            "vøȼȺƀᵾłȺɍɏ": "𝓰𝓸𝓸𝓭",
            "ﻭɼค๓๓คɼ": "єχ¢єℓℓєηт",
        }
        feedback = {
            "feedback": "𝕿𝖍𝖎𝖘 𝖎𝖘 𝖘𝖔𝖒𝖊 𝖋𝖊𝖊𝖉𝖇𝖆𝖈𝖐."
        }
        AssessmentPart.create_from_option_names(
            assessment, selected, feedback=feedback
        )

        # Check the score (the feedback-only assessment should count for 0 points)
        self.assertEqual(assessment.points_earned, 3)
        self.assertEqual(assessment.points_possible, 4)

        # Check the feedback text
        feedback_only = AssessmentPart.objects.get(criterion__name="feedback")
        self.assertEqual(feedback_only.feedback, "𝕿𝖍𝖎𝖘 𝖎𝖘 𝖘𝖔𝖒𝖊 𝖋𝖊𝖊𝖉𝖇𝖆𝖈𝖐.")

    def test_create_with_all_feedback_only_criteria(self):
        rubric = self._rubric_with_all_feedback_only_criteria()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Create assessment parts, each of which are feedback-only (no points)
        selected = {}
        feedback = {
            "vøȼȺƀᵾłȺɍɏ": "𝓰𝓸𝓸𝓭",
            "ﻭɼค๓๓คɼ": "єχ¢єℓℓєηт",
        }
        AssessmentPart.create_from_option_names(
            assessment, selected, feedback=feedback
        )

        # Check the score (should be 0, since we haven't selected any points)
        self.assertEqual(assessment.points_earned, 0)
        self.assertEqual(assessment.points_possible, 0)

    def test_create_from_option_points_feedback_only_criterion(self):
        rubric = self._rubric_with_one_feedback_only_criterion()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Create assessment parts by providing scores for options
        # but NO feedback.  This simulates how an example-based AI
        # assessment is created.
        selected = {
            "vøȼȺƀᵾłȺɍɏ": 2,
            "ﻭɼค๓๓คɼ": 1,
        }
        AssessmentPart.create_from_option_points(assessment, selected)

        # Check the score (the feedback-only assessment should count for 0 points)
        self.assertEqual(assessment.points_earned, 3)
        self.assertEqual(assessment.points_possible, 4)

        # Check the feedback text (should default to an empty string)
        feedback_only = AssessmentPart.objects.get(criterion__name="feedback")
        self.assertEqual(feedback_only.feedback, "")

    def test_create_from_option_points_all_feedback_only_criteria(self):
        rubric = self._rubric_with_all_feedback_only_criteria()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Since there are no criteria with options, and we're not
        # providing written feedback, pass in an empty selection.
        selected = {}
        AssessmentPart.create_from_option_points(assessment, selected)

        # Score should be zero, since none of the criteria have options
        self.assertEqual(assessment.points_earned, 0)
        self.assertEqual(assessment.points_possible, 0)

    def test_default_feedback_for_feedback_only_criterion(self):
        rubric = self._rubric_with_one_feedback_only_criterion()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Create assessment parts, but do NOT provide any feedback
        # This simulates how non-peer assessments are created
        # Note that this is different from providing an empty feedback dict;
        # here, we're not providing the `feedback` kwarg at all.
        selected = {
            "vøȼȺƀᵾłȺɍɏ": "𝓰𝓸𝓸𝓭",
            "ﻭɼค๓๓คɼ": "єχ¢єℓℓєηт",
        }
        AssessmentPart.create_from_option_names(assessment, selected)

        # Check the score (the feedback-only assessment should count for 0 points)
        self.assertEqual(assessment.points_earned, 3)
        self.assertEqual(assessment.points_possible, 4)

        # Check the feedback text, which should default to an empty string
        feedback_only = AssessmentPart.objects.get(criterion__name="feedback")
        self.assertEqual(feedback_only.feedback, "")

    def test_no_feedback_provided_for_feedback_only_criterion(self):
        rubric = self._rubric_with_one_feedback_only_criterion()
        assessment = Assessment.create(rubric, "Bob", "submission UUID", "PE")

        # Create assessment parts
        # Do NOT provide feedback for the feedback-only criterion
        selected = {
            "vøȼȺƀᵾłȺɍɏ": "𝓰𝓸𝓸𝓭",
            "ﻭɼค๓๓คɼ": "єχ¢єℓℓєηт",
        }
        feedback = {}

        # Expect an error when we try to create the assessment parts
        with self.assertRaises(InvalidRubricSelection):
            AssessmentPart.create_from_option_names(assessment, selected, feedback=feedback)

    def _rubric_with_one_feedback_only_criterion(self):
        """Create a rubric with one feedback-only criterion."""
        rubric_dict = copy.deepcopy(RUBRIC)
        rubric_dict['criteria'].append({
            "order_num": 2,
            "name": "feedback",
            "prompt": "only feedback, no points",
            "options": []
        })
        return rubric_from_dict(rubric_dict)

    def _rubric_with_all_feedback_only_criteria(self):
        """Create a rubric with all feedback-only criteria."""
        rubric_dict = copy.deepcopy(RUBRIC)
        for criterion in rubric_dict['criteria']:
            criterion['options'] = []
        return rubric_from_dict(rubric_dict)

    @ddt.file_data('data/models_check_criteria_assessed.json')
    def test_check_all_criteria_assessed(self, data):
        student_item = {
            'student_id': '𝖙𝖊𝖘𝖙 𝖚𝖘𝖊𝖗',
            'item_id': 'test_item',
            'course_id': 'test_course',
            'item_type': 'test_type'
        }
        submission = create_submission(student_item, "Test answer")

        rubric, options_selected, criterion_feedback = self._create_data_structures_with_criterion_properties(
            has_option_selected=data['has_option_selected'],
            has_zero_options=data['has_zero_options'],
            has_feedback=data['has_feedback']
        )
        error = False
        try:
            create_assessment(
                submission['uuid'], student_item['student_id'], options_selected,
                criterion_feedback, "overall feedback", rubric
            )
        except SelfAssessmentRequestError:
            error = True
        self.assertEqual(data['expected_error'], error)

    def _create_data_structures_with_criterion_properties(  # pylint: disable=invalid-name
            self,
            has_option_selected=True,
            has_zero_options=True,
            has_feedback=True
    ):
        """
        Generates a dummy set of criterion definition structures that will allow us to specificy a specific combination
        of criterion attributes for a test case.
        """
        options = []
        if not has_zero_options:
            options = [{
                "name": "Okay",
                "points": 1,
                "description": "It was okay I guess."
            }]

        rubric = {
            'criteria': [
                {
                    "name": "Quality",
                    "prompt": "How 'good' was it?",
                    "options": options
                }
            ]
        }

        options_selected = {}
        if has_option_selected:
            options_selected['Quality'] = 'Okay'

        criterion_feedback = {}
        if has_feedback:
            criterion_feedback['Quality'] = "This was an assignment of average quality."

        return rubric, options_selected, criterion_feedback
