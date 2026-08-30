"""Exception hierarchy.

Rule: every recoverable failure raises a specific subclass; CLI boundaries catch
RTAIError once and map it to an exit code (see rtai_core.cli.ExitCode).
"""


class RTAIError(Exception):
    """Base class for every error raised intentionally by this suite."""

    exit_code = 70


class ConfigError(RTAIError):
    """Invalid or missing configuration (files, env, CLI merge)."""

    exit_code = 78


class ValidationError(RTAIError):
    """A value failed semantic validation (domain, email, profile field)."""

    exit_code = 64


class AuthError(RTAIError):
    """Authorization attestation missing, invalid, or refused."""

    exit_code = 77


class ProviderError(RTAIError):
    """Upstream LLM provider failed after retries, or misconfigured."""

    exit_code = 69


class TargetError(RTAIError):
    """The system under test is unreachable or returned malformed output."""

    exit_code = 75


class StorageError(RTAIError):
    """Local persistence (JSONL/SQLite) failed."""

    exit_code = 74
