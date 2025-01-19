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
