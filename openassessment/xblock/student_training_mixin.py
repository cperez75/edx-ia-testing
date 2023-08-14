"""
Student training step in the OpenAssessment XBlock.
"""
import logging
from webob import Response
from xblock.core import XBlock

from openassessment.assessment.api import student_training
from openassessment.workflow.errors import AssessmentWorkflowError
from openassessment.xblock.data_conversion import convert_training_examples_list_to_dict, create_submission_dict

from .resolve_dates import DISTANT_FUTURE
from .user_data import get_user_preferences
from .api.assessment.student_training import StudentTrainingApi

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class StudentTrainingMixin:
    """
    Student training is a step that allows students to practice
    assessing example essays provided by the course author.

    1) A student is shown an example essay.
    2) The student scores the example essay.
        a) If the student's scores match the instructor's scores,
            the student is shown the next example.  If there are no
            more examples, the step is marked complete.
        b) If the student's scores do NOT match the instructor's scores,
            the student is prompted to retry.

    """

    @XBlock.handler
    def render_student_training(self, data, suffix=''):   # pylint:disable=W0613
        """
        Render the student training step.

        Args:
            data: Not used.

        Keyword Arguments:
            suffix: Not used.

        Returns:
            unicode: HTML content of the grade step

        """
        if "student-training" not in self.assessment_steps:
            return Response("")

        try:
            path, context = self.training_path_and_context()
        except Exception:  # pylint: disable=broad-except
            msg = f"Could not render Learner Training step for submission {self.submission_uuid}."
            logger.exception(msg)
            return self.render_error(self._("An unexpected error occurred."))
        else:
            return self.render_assessment(path, context)

    def training_path_and_context(self):
        """
        Return the template path and context used to render the student training step.

        Returns:
            tuple of `(path, context)` where `path` is the path to the template and
                `context` is a dict.

        """
        step_data = StudentTrainingAPI(self)

        # Retrieve the status of the workflow.
        # If no submissions have been created yet, the status will be None.

        user_preferences = get_user_preferences(self.runtime.service(self, 'user'))

        context = {"xblock_id": self.get_xblock_id()}
        template = 'openassessmentblock/student_training/student_training_unavailable.html'

        context['allow_multiple_files'] = self.allow_multiple_files
        # add allow_latex field to the context
        context['allow_latex'] = self.allow_latex
        context['prompts_type'] = self.prompts_type
        context['user_timezone'] = user_preferences['user_timezone']
        context['user_language'] = user_preferences['user_language']

        if not step_data.has_workflow:
            return template, context

        # If the student has completed the training step, then show that the step is complete.
        # We put this condition first so that if a student has completed the step, it *always*
        # shows as complete.
        # We're assuming here that the training step always precedes the other assessment steps
        # (peer/self) -- we may need to make this more flexible later.
        if step_data.is_cancelled:
            template = 'openassessmentblock/student_training/student_training_cancelled.html'
        elif step_data.is_complete:
            template = 'openassessmentblock/student_training/student_training_complete.html'

        # If the problem is closed, then do not allow students to access the training step
        elif step_data.is_not_available_yet:
            context['training_start'] = step_data.start_date
            template = 'openassessmentblock/student_training/student_training_unavailable.html'
        elif step_data.is_past_due:
            context['training_due'] = step_data.due_date
            template = 'openassessmentblock/student_training/student_training_closed.html'

        # If we're on the training step, show the student an example
        # We do this last so we can avoid querying the student training API if possible.
        else:
            if not step_data.training_module:
                return template, context

            if step_data.is_due:
                context['training_due'] = step_data.due_date

            # Report progress in the student training workflow (completed X out of Y)
            context['training_num_available'] = step_data.num_available
            context['training_num_completed'] = step_data.num_completed
            context['training_num_current'] = context['training_num_completed'] + 1

            # Retrieve the example essay for the student to submit
            # This will contain the essay text, the rubric, and the options the instructor selected.
            example_context = step_data.example_context
            if example_context.error_message:
                logger.error(example_context.error_message)
                template = "openassessmentblock/student_training/student_training_error.html"
            else:
                context['training_essay'] = example_context.essay_context
                context['training_rubric'] = step_data.example_rubric 
                template = 'openassessmentblock/student_training/student_training.html'

        return template, context

    @XBlock.json_handler
    def training_assess(self, data, suffix=''):  # pylint:disable=W0613
        """
        Compare the scores given by the student with those given by the course author.
        If they match, update the training workflow.  The client can then reload this
        step to view the next essay or the completed step.

        Currently, we return a boolean indicating whether the student assessed correctly
        or not.  However, the student training API provides the exact criteria that the student
        scored incorrectly, as well as the "correct" options for those criteria.
        In the future, we may expose this in the UI to provide more detailed feedback.

        Args:
            data (dict): Must have the following keys:
                options_selected (dict): Dictionary mapping criterion names to option values.

        Returns:
            Dict with keys:
                * "success" (bool) indicating success or error
                * "msg" (unicode) containing additional information if an error occurs.
                * "correct" (bool) indicating whether the student scored the assessment correctly.

        """
        if 'options_selected' not in data:
            return {'success': False, 'msg': self._("Missing options_selected key in request")}
        if not isinstance(data['options_selected'], dict):
            return {'success': False, 'msg': self._("options_selected must be a dictionary")}

        # Check the student's scores against the course author's scores.
        # This implicitly updates the student training workflow (which example essay is shown)
        # as well as the assessment workflow (training/peer/self steps).
        try:
            corrections = student_training.assess_training_example(
                self.submission_uuid, data['options_selected']
            )
            self.runtime.publish(
                self,
                "openassessment.student_training_assess_example",
                {
                    "submission_uuid": self.submission_uuid,
                    "options_selected": data["options_selected"],
                    "corrections": corrections
                }
            )
        except student_training.StudentTrainingRequestError:
            msg = (
                "Could not check learner training scores for the learner with submission UUID {uuid}"
            ).format(uuid=self.submission_uuid)
            logger.warning(msg, exc_info=True)
            return {
                'success': False,
                'msg': self._("Your scores could not be checked.")
            }
        except student_training.StudentTrainingInternalError:
            return {
                'success': False,
                'msg': self._("Your scores could not be checked.")
            }
        except Exception:  # pylint: disable=broad-except
            return {
                'success': False,
                'msg': self._("An unexpected error occurred.")
            }
        else:
            try:
                self.update_workflow_status()
            except AssessmentWorkflowError:
                msg = self._('Could not update workflow status.')
                logger.exception(msg)
                return {'success': False, 'msg': msg}
            return {
                'success': True,
                'msg': '',
                'corrections': corrections,
            }
