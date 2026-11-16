"""One catalog frame for every upload.

Square sRGB JPEG: the subject is contained and centered on white.
Small sources are not upscaled. Metal color is left as shot.
"""

from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageCms, ImageFilter, ImageOps

FULL_SIDE = 1200
PREVIEW_SIDE = 400
FULL_QUALITY = 85
PREVIEW_QUALITY = 80
MARGIN_RATIO = 0.06
WHITE = (255, 255, 255)


def normalize_catalog_photos(raw: bytes) -> tuple[bytes, bytes]:
    image = _open_rgb(raw)
    full = _render(image, side=FULL_SIDE, quality=FULL_QUALITY, subsampling=0)
    preview = _render(image, side=PREVIEW_SIDE, quality=PREVIEW_QUALITY, subsampling=2)
    return full, preview


def _open_rgb(raw: bytes) -> Image.Image:
    try:
        with Image.open(BytesIO(raw)) as source:
            source.seek(0)
            image = ImageOps.exif_transpose(source)
            if image is None:
                raise ValueError("empty image")
            image = _to_srgb(image)
            return _flatten_on_white(image)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Can't read image") from exc


def _to_srgb(image: Image.Image) -> Image.Image:
    profile_bytes = image.info.get("icc_profile")
    if not profile_bytes or image.mode not in ("RGB", "RGBA", "L", "CMYK"):
        return image
    try:
        source = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
        target = ImageCms.createProfile("sRGB")
        return ImageCms.profileToProfile(image, source, target, outputMode=image.mode)
    except Exception:
        return image


def _flatten_on_white(image: Image.Image) -> Image.Image:
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, WHITE)
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if image.mode == "RGB":
        return image.copy()
    return image.convert("RGB")


def _render(image: Image.Image, *, side: int, quality: int, subsampling: int) -> bytes:
    margin = round(side * MARGIN_RATIO)
    inner = max(1, side - margin * 2)
    fitted = image.copy()
    source_size = fitted.size
    fitted.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    if fitted.size != source_size:
        fitted = fitted.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=3))

    canvas = Image.new("RGB", (side, side), WHITE)
    left = (side - fitted.width) // 2
    top = (side - fitted.height) // 2
    canvas.paste(fitted, (left, top))

    output = BytesIO()
    canvas.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling=subsampling,
    )
    return output.getvalue()
