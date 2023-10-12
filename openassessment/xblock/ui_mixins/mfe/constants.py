"""
Constants used in the ORA MFE BFF
"""


class ErrorCodes:
    INCORRECT_PARAMETERS = "ERR_WRONG_PARAMS"
    INVALID_RESPONSE_SHAPE = "ERR_INCORRECT_RESPONSE_SHAPE"
    INTERNAL_EXCEPTION = "ERR_INTERNAL"
    UNKNOWN_SUFFIX = "ERR_SUFFIX"
    IN_STUDIO_PREVIEW = "ERR_IN_STUDIO_PREVIEW"
    MULTIPLE_SUBMISSIONS = "ERR_MULTIPLE_SUBISSIONS"
    SUBMISSION_TOO_LONG = "ERR_SUBMISSION_TOO_LONG"
    SUBMISSION_API_ERROR = "ERR_SUBMISSION_API"
    EMPTY_ANSWER = "ERR_EMPTY_ANSWER"
    UNKNOWN_ERROR = "ERR_UNKNOWN"