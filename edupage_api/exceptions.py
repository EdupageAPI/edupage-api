class NotLoggedInException(Exception):
    pass


class MissingDataException(Exception):
    pass


class BadCredentialsException(Exception):
    pass


class NotAnOnlineLessonError(Exception):
    pass


class FailedToRateException(Exception):
    pass


class FailedToChangeMealError(Exception):
    pass


class FailedToUploadFileException(Exception):
    pass


class FailedToParseGradeDataError(Exception):
    pass


class ExpiredSessionException(Exception):
    pass


class InvalidTeacherException(Exception):
    pass


class RequestError(Exception):
    pass


class RetryLaterException(RequestError):
    def __init__(self, message: str, retry_in_seconds: int):
        super().__init__(message)
        self.retry_in_seconds = retry_in_seconds


class InvalidMealsData(Exception):
    pass


class Base64DecodeError(Exception):
    pass


class InvalidRecipientsException(Exception):
    pass


class InvalidChildException(Exception):
    pass


class UnknownServerError(Exception):
    pass


class NotParentException(Exception):
    pass


class SecondFactorFailedException(Exception):
    pass


class InsufficientPermissionsException(Exception):
    pass


class CaptchaException(Exception):
    pass


class ConsultationError(Exception):
    """A consultation request could not be completed safely."""

    code = "consultation_rejected"


class ConsultationSlotTaken(ConsultationError):
    code = "slot_taken"


class ConsultationClosed(ConsultationError):
    code = "booking_closed"


class ConsultationLimitReached(ConsultationError):
    code = "booking_limit"


class ConsultationNotOwned(ConsultationError):
    code = "booking_not_owned"


class ConsultationUncertain(ConsultationError):
    """A write may have succeeded; inspect the account before retrying."""

    code = "booking_uncertain"


class ConsultationSlotNotFound(ConsultationError):
    code = "slot_not_found"
