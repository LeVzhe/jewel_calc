import aioboto3
from botocore.config import Config

from core.settings import Settings, settings


class R2Storage:
    def __init__(self, app_settings: Settings):
        self.bucket = app_settings.R2_BUCKET_NAME
        self.public_base = app_settings.R2_PUBLIC_BASE_URL
        self.session = aioboto3.Session()
        self._client_kwargs = {
            "endpoint_url": app_settings.R2_ENDPOINT_URL,
            "aws_access_key_id": app_settings.R2_ACCESS_KEY_ID,
            "aws_secret_access_key": app_settings.R2_SECRET_ACCESS_KEY,
            "region_name": "auto",
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        }

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ContentLength=len(data),
            )
        return f"{self.public_base.rstrip('/')}/{key}"

    async def delete(self, key: str) -> None:
        async with self.session.client("s3", **self._client_kwargs) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)


r2_storage = R2Storage(settings)
