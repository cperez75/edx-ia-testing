"""
External API for ORA Student Training data
"""

import logging
from ieia.assessment.api.student_training import (
    get_num_completed,
    get_training_example,
    assess_training_example,
)
from ieia.assessment.errors.student_training import StudentTrainingError
from ieia.workflow.errors import AssessmentWorkflowError
from ieia.xblock.utils.data_conversion import (
    convert_training_examples_list_to_dict,
    create_submission_dict,
)
from ieia.xblock.apis.step_data_api import StepDataAPI


logger = logging.getLogger(__name__)


class StudentTrainingAPI(StepDataAPI):
    def __init__(self, block):
        super().__init__(block, "student-training")

    def __repr__(self):
        if self.training_module:
            return "{0}".format(
                {
                    "due_date": self.due_date,
                    "has_workflow": self.has_workflow,
                    "is_cancelled": self.is_cancelled,
                    "is_complete": self.is_complete,
                    "is_due": self.is_due,
                    "is_not_available_yet": self.is_not_available_yet,
                    "is_past_due": self.is_past_due,
                    "num_available": self.num_available,
                    "num_completed": self.num_completed,
                    "start_date": self.start_date,
                    "training_module": self.training_module,
                }
            )
        return "{0}".format(
            {
                "due_date": self.due_date,
                "has_workflow": self.has_workflow,
                "is_cancelled": self.is_cancelled,
                "is_complete": self.is_complete,
                "is_due": self.is_due,
                "is_not_available_yet": self.is_not_available_yet,
                "is_past_due": self.is_past_due,
                "start_date": self.start_date,
                "training_module": self.training_module,
            }
        )

    @property
    def example(self):
        return get_training_example(
            self._block.submission_uuid,
            {
                "prompt": self.config_data.prompt,
                "criteria": self._block.rubric_criteria_with_labels,
            },
            self.examples,
        )

    @property
    def example_context(self):
        context, error_message = self._parse_example(self.example)
        return {"error_message": error_message, "essay_context": context}

    @property
    def example_rubric(self):
        rubric = self.example["rubric"]
        return {
            "criteria": rubric["criteria"],
            "points_possible": rubric["points_possible"],
        }

    @property
    def examples(self):
        return convert_training_examples_list_to_dict(self.training_module["examples"])

    @property
    def has_workflow(self):
        return self.workflow_data.has_status

    @property
    def is_cancelled(self):
        return self.workflow_data.is_cancelled

    @property
    def is_complete(self):
        state = self.workflow_data
        return state.has_status and not (state.is_cancelled or state.is_training)

    @property
    def num_available(self):
        return len(self.training_module["examples"])

    @property
    def num_completed(self):
        return get_num_completed(self._block.submission_uuid)

    @property
    def training_module(self):
        return self.config_data.get_assessment_module("student-training")

    def _parse_answer_dict(self, answer):
        """
        Helper to parse answer as a fully-qualified dict.
        """
        parts = answer.get("parts", [])
        if parts and isinstance(parts[0], dict):
            if isinstance(parts[0].get("text"), str):
                return create_submission_dict({"answer": answer}, self.config_data.prompts)
        return None

    def _parse_answer_list(self, answer):
        """
        Helper to parse answer as a list of strings.
        """
        if answer and isinstance(answer[0], str):
            return self._parse_answer_string(answer[0])
        elif not answer:
            return self._parse_answer_string("")
        return None

    def _parse_answer_string(self, answer):
        """
        Helper to parse answer as a plain string
        """
        return create_submission_dict({"answer": {"parts": [{"text": answer}]}}, self.config_data.prompts)

    def _parse_example(self, example):
        """
        EDUCATOR-1263: examples are serialized in a myriad of different ways, we need to be robust to all of them.

        Types of serialized example['answer'] we handle here:
        -fully specified: {'answer': {'parts': [{'text': <response_string>}]}}
        -list of string: {'answer': [<response_string>]}
        -just a string: {'answer': <response_string>}
        """
        if not example:
            return (
                {},
                "No training example was returned from the API for student with Submission UUID {}".format(
                    self._block.submission_uuid
                ),
            )
        answer = example["answer"]
        submission_dict = None
        if isinstance(answer, str):
            submission_dict = self._parse_answer_string(answer)
        elif isinstance(answer, dict):
            submission_dict = self._parse_answer_dict(answer)
        elif isinstance(answer, list):
            submission_dict = self._parse_answer_list(answer)
        return (submission_dict, "") or (
            {},
            f"Improperly formatted example, cannot render student training.  Example: {example}",
        )


def training_assess(
    options_selected,
    config_data,
    workflow_data,
):
    """
    Compare the scores given by the student with those given by the course author.
    If they match, update the training workflow.  The client can then reload this
    step to view the next essay or the completed step.

    Args:
        options_selected: (dict) Mapping of criterion name to selected option name
        config_data: ConfigDataApi Object
        workflow_data: WorkflowDataApi Object

    Returns:
        (dict) Mapping of criterion name to defined "correct" option name, for any criterion in options_selected
        that does not match the defined answers

    Raises:
        StudentTrainingError
        AssessmentWorkflowError
        Exception
    """
    # Check the student's scores against the course author's scores.
    # This implicitly updates the student training workflow (which example essay is shown)
    # as well as the assessment workflow (training/peer/self steps).
    submission_uuid = workflow_data.submission_uuid
    try:
        corrections = assess_training_example(submission_uuid, options_selected)
        config_data.publish_event(
            "ieia.student_training_assess_example",
            {
                "submission_uuid": submission_uuid,
                "options_selected": options_selected,
                "corrections": corrections,
            },
        )
    except StudentTrainingError:
        msg = "Could not check learner training scores for the learner with submission UUID %s"
        logger.warning(msg, submission_uuid, exc_info=True)
        raise

    try:
        workflow_data.update_workflow_status()
    except AssessmentWorkflowError:
        logger.exception("Could not update workflow status for submission uuid %s", submission_uuid)
        raise
    return corrections
