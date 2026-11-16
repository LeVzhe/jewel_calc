from uuid import UUID


def object_keys(folder: str, guid: UUID) -> tuple[str, str]:
    prefix = f"{folder}/{guid}"
    return f"{prefix}/{guid}_image.jpg", f"{prefix}/{guid}_preview.jpg"
