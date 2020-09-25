"""Sengled Bulb Integration."""


class Error(Exception):
    """Base class for other exceptions"""

    pass


class SengledApiError(Error):
    """Raised when the api returns an error"""

    pass


class AccessTokenError(SengledApiError):
    """Raised when the api returns an AccessTokenError"""

    pass


class SengledApiAccessToken:
    pass
