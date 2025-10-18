"""Custom exceptions for skill-mcp server."""


class SkillMCPException(Exception):
    """Base exception for skill-mcp."""
    pass


class SkillNotFoundError(SkillMCPException):
    """Raised when a skill does not exist."""
    pass


class FileNotFoundError(SkillMCPException):
    """Raised when a file does not exist in a skill."""
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
