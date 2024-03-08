"""
Assessment API Errors
"""

from ieia.assessment.errors import AssessmentError


class InvalidStateToAssess(AssessmentError):
    pass


class ReviewerMustHaveSubmittedException(InvalidStateToAssess):
    pass


class ServerClientUUIDMismatchException(AssessmentError):
    pass
