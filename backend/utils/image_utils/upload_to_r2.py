import logging
from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import HTTPException

from utils.image_utils.decode_base64 import decode_base64_image
from utils.image_utils.keys import object_keys
from utils.image_utils.normalize import normalize_catalog_photos
from utils.r2_service import r2_storage

logger = logging.getLogger(__name__)

_CONTENT_TYPE = "image/jpeg"


async def upload_images_to_r2_pipeline(image_base64: str, guid: UUID, r2_folder: str) -> dict[str, str | bool]:
    raw = decode_base64_image(image_base64)
    full, preview = normalize_catalog_photos(raw)
    image_key, preview_key = object_keys(r2_folder, guid)

    try:
        image_url = await r2_storage.upload(image_key, full, _CONTENT_TYPE)
        preview_url = await r2_storage.upload(preview_key, preview, _CONTENT_TYPE)
    except HTTPException:
        raise
    except ClientError as exc:
        logger.error("R2 upload failed. CAUSE=%s", exc)
        raise HTTPException(status_code=502, detail="Failed to upload images") from exc
    except Exception as exc:
        logger.exception("Image pipeline failed. CAUSE=%s", exc)
        raise HTTPException(status_code=400, detail="Can't process image") from exc

    return {
        "image": image_url,
        "image_preview": preview_url,
        "image_on_s3": True,
        "image_preview_on_s3": True,
    }
