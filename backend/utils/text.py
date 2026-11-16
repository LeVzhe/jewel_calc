from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clean_spaces(value: str) -> str:
    return " ".join(value.split())


def like_contains(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
