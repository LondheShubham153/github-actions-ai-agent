"""Secret redaction and untrusted-data wrapping, shared by memory and GitHub code."""
import re

_SECRETS = re.compile(
    r"(gh[pos]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}"
    r"|Bearer\s+[A-Za-z0-9._~+/=-]+"
    r"|(?i:password|token|secret|api[_-]?key)\s*[=:]\s*\S+"
    r"|[\w.+-]+@[\w-]+\.[\w.-]+)"
)


def redact(text: str) -> str:
    return _SECRETS.sub("[REDACTED]", text)


def wrap(label: str, text: str) -> str:
    """Mark text as untrusted reference data before the model sees it."""
    return f"<untrusted_{label}>\n{text}\n</untrusted_{label}>"
