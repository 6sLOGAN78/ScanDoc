"""
CLI exception hierarchy with exit code mapping.
"""

from scandoc.cli.taxonomy import ExitCode


class CliError(Exception):
    """Base Exception for CLI errors."""

    def __init__(self, message: str, exit_code: ExitCode = ExitCode.PROCESSING_ERROR):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class InvalidArgumentsError(CliError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=ExitCode.INVALID_ARGUMENTS)


class InputError(CliError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=ExitCode.INPUT_ERROR)


class ProcessingError(CliError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=ExitCode.PROCESSING_ERROR)


class ConfigurationError(CliError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=ExitCode.CONFIGURATION_ERROR)


class ProviderModelError(CliError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=ExitCode.PROVIDER_MODEL_ERROR)
