class DiddiGoError(Exception):
    """Base application error."""


class NotFoundError(DiddiGoError):
    """Raised when a resource cannot be found."""
