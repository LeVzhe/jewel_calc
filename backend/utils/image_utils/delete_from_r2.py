import logging
from uuid import UUID

from utils.image_utils.keys import object_keys
from utils.r2_service import r2_storage

logger = logging.getLogger(__name__)


async def delete_images_by_guid(guid: UUID, folder: str) -> None:
    for key in object_keys(folder, guid):
        try:
            await r2_storage.delete(key)
        except Exception as exc:
            logger.error("R2 cleanup failed for key=%s. CAUSE=%s", key, exc)
