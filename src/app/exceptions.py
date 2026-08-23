class AppError(Exception):
    """Base class for exceptions in this module."""


class NotFoundError(AppError):
    pass


class EmailAlreadyExistsError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass

class BookingConflictError(AppError):
    pass
