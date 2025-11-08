"""Custom exceptions for skill-mcp server."""


class SkillMCPException(Exception):
    """Base exception for skill-mcp."""

    pass


class SkillNotFoundError(SkillMCPException):
    """Raised when a skill does not exist."""

    pass


class SkillAlreadyExistsError(SkillMCPException):
    """Raised when trying to create a skill that already exists."""

    pass


class FileNotFoundError(SkillMCPException):
    """Raised when a file does not exist in a skill."""

    pass


class FileOperationError(SkillMCPException):
    """Raised when a file operation fails."""

    pass


class PathTraversalError(SkillMCPException):
    """Raised when a path traversal attack is detected."""

    pass


class InvalidPathError(SkillMCPException):
    """Raised when a path is invalid."""

    pass


class FileTooBigError(SkillMCPException):
    """Raised when a file exceeds size limits."""

    pass


class ScriptExecutionError(SkillMCPException):
    """Raised when script execution fails."""

    pass


class EnvFileError(SkillMCPException):
    """Raised when .env file operations fail."""

    pass


class ProtectedFileError(SkillMCPException):
    """Raised when attempting to delete a protected file."""

    pass


class InvalidTemplateError(SkillMCPException):
    """Raised when an invalid template name is provided."""

    pass
