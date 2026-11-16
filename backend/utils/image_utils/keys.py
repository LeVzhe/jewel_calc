from uuid import UUID

from utils.constants import R2Folders


def jewelry_photo_folder(jewelry_guid: UUID) -> str:
    return f"{R2Folders.JEWELRY}/{jewelry_guid}"


def object_keys(folder: str, guid: UUID) -> tuple[str, str]:
    prefix = f"{folder}/{guid}"
    return f"{prefix}/{guid}_image.jpg", f"{prefix}/{guid}_preview.jpg"
