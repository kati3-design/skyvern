from datetime import datetime

from skyvern.config import settings
from skyvern.forge.sdk.api.aws import AsyncAWSClient
from skyvern.forge.sdk.artifact.models import Artifact, ArtifactType
from skyvern.forge.sdk.artifact.storage.base import FILE_EXTENTSION_MAP, BaseStorage
from skyvern.forge.sdk.models import Step


class S3Storage(BaseStorage):
    def __init__(self, bucket: str | None = None) -> None:
        self.async_client = AsyncAWSClient()
        self.bucket = bucket or settings.AWS_S3_BUCKET_ARTIFACTS

    def build_uri(self, artifact_id: str, step: Step, artifact_type: ArtifactType) -> str:
        file_ext = FILE_EXTENTSION_MAP[artifact_type]
        return f"s3://{self.bucket}/{settings.ENV}/{step.task_id}/{step.order:02d}_{step.retry_index}_{step.step_id}/{datetime.utcnow().isoformat()}_{artifact_id}_{artifact_type}.{file_ext}"

    async def store_artifact(self, artifact: Artifact, data: bytes) -> None:
        await self.async_client.upload_file(artifact.uri, data)

    async def retrieve_artifact(self, artifact: Artifact) -> bytes | None:
        return await self.async_client.download_file(artifact.uri)

    async def get_share_link(self, artifact: Artifact) -> str | None:
        share_urls = await self.async_client.create_presigned_urls([artifact.uri])
        return share_urls[0] if share_urls else None

    async def get_share_links(self, artifacts: list[Artifact]) -> list[str] | None:
        return await self.async_client.create_presigned_urls([artifact.uri for artifact in artifacts])

    async def store_artifact_from_path(self, artifact: Artifact, path: str) -> None:
        await self.async_client.upload_file_from_path(artifact.uri, path)

    async def save_streaming_file(self, organization_id: str, file_name: str) -> None:
        from_path = f"{settings.STREAMING_FILE_BASE_PATH}/{organization_id}/{file_name}"
        to_path = f"s3://{settings.AWS_S3_BUCKET_SCREENSHOTS}/{settings.ENV}/{organization_id}/{file_name}"
        await self.async_client.upload_file_from_path(to_path, from_path)

    async def get_streaming_file(self, organization_id: str, file_name: str, use_default: bool = True) -> bytes | None:
        path = f"s3://{settings.AWS_S3_BUCKET_SCREENSHOTS}/{settings.ENV}/{organization_id}/{file_name}"
        return await self.async_client.download_file(path, log_exception=False)
