"""Application-level errors safe to display to users."""


class AICLIError(Exception):
    """Base class for expected, user-facing failures."""


class ConfigurationError(AICLIError):
    """Configuration is missing or invalid."""


class CredentialError(ConfigurationError):
    """Provider credentials are missing or rejected."""


class InputError(AICLIError):
    """CLI input cannot be used."""


class OutputError(AICLIError):
    """Generated content cannot be written."""


class ProviderError(AICLIError):
    """A provider request failed without exposing provider internals."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable
