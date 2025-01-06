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


class SengledApiAccessToken(SengledApiError):
    """Raised when the api encounters issues with the AccessToken."""

    def __init__(self, message="Invalid or missing AccessToken"):
        self.message = message
        super().__init__(self.message)
