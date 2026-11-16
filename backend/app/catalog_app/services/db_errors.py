from typing import NoReturn

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def raise_integrity(error: IntegrityError, *, constraint: str, conflict_detail: str) -> NoReturn:
    origin = getattr(error, "orig", None)
    constraint_name = str(getattr(origin, "constraint_name", "") or "")
    raw = f"{constraint_name} {origin}".lower()
    if constraint in raw:
        raise HTTPException(status_code=409, detail=conflict_detail) from error
    raise HTTPException(status_code=400, detail="Data conflict") from error
