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


class FailedToChangeLunchError(Exception):
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


class InvalidLunchData(Exception):
    pass
