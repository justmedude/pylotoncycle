class PylotonCycleError(Exception):
    """Base exception for pylotoncycle."""


class PelotonAuthError(PylotonCycleError):
    """Raised when authentication or token refresh fails."""


class PelotonAPIError(PylotonCycleError):
    """Raised when the API returns an unexpected response."""
