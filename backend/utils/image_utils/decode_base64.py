import base64
import re

from fastapi import HTTPException

_DATA_URL_RE = re.compile(r"^data:image/[\w+.-]+;base64,", re.I)
_MAX_BYTES = 10 * 1024 * 1024
_MAX_TEXT = 20_000_000


def decode_base64_image(value: str) -> bytes:
    if len(value) > _MAX_TEXT:
        raise HTTPException(status_code=400, detail="Image too large")

    raw_b64 = _DATA_URL_RE.sub("", value.strip())
    try:
        data = base64.b64decode(raw_b64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image_base64") from exc

    if not data:
        raise HTTPException(status_code=400, detail="Empty image_base64")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image too large")
    return data
