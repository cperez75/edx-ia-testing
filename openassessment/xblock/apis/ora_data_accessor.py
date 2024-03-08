"""API Data wrapper for exposed APIs within ORA XBlock"""
from ieia.xblock.apis.grades_api import GradesAPI
from ieia.xblock.apis.ora_config_api import ORAConfigAPI
from ieia.xblock.apis.submissions.submissions_api import SubmissionAPI
from ieia.xblock.apis.assessments.peer_assessment_api import PeerAssessmentAPI
from ieia.xblock.apis.assessments.self_assessment_api import SelfAssessmentAPI
from ieia.xblock.apis.assessments.staff_assessment_api import (
    StaffAssessmentAPI,
)
from ieia.xblock.apis.assessments.student_training_api import (
    StudentTrainingAPI,
)


class ORADataAccessor:
    def __init__(self, block):
        self._block = block

    @property
    def config_data(self):
        return ORAConfigAPI(self._block)

    @property
    def submission_data(self):
        return SubmissionAPI(self._block)

    @property
    def workflow_data(self):
        return self._block.workflow_data

    @property
    def grades_data(self):
        return GradesAPI(self._block)

    @property
    def self_assessment_data(self):
        return SelfAssessmentAPI(self._block)

    @property
    def staff_assessment_data(self):
        return StaffAssessmentAPI(self._block)

    @property
    def student_training_data(self):
        return StudentTrainingAPI(self._block)

    def peer_assessment_data(self, continue_grading=False):
        return PeerAssessmentAPI(self._block, continue_grading)
