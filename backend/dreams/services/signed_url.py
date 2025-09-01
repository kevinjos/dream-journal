"""Service for generating signed URLs for Google Cloud Storage."""

import json
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from google.cloud import storage

from dreams.models import Image


class SignedUrlService:
    """Service for generating signed URLs for GCS access."""

    def __init__(self) -> None:
        self.bucket_name = settings.GCS_BUCKET_NAME
        if settings.SERVICE_ACCOUNT_JSON:
            self.storage_client = storage.Client.from_service_account_info(
                json.loads(settings.SERVICE_ACCOUNT_JSON)
            )
            self.bucket = self.storage_client.bucket(self.bucket_name)

    def get_signed_url(
        self, dream_image: Image, method: str = "GET", expiration_hours: int = 1
    ) -> str:
        """
        Generate a signed URL for accessing an image in GCS.

        Args:
            dream_image: The Image model instance
            method: HTTP method for the signed URL (GET, PUT, DELETE, etc.)
            expiration_hours: Hours until URL expires (default: 1)

        Returns:
            Signed URL string for the specified operation
        """
        blob = self.bucket.blob(dream_image.gcs_path)
        expiration = timezone.now() + timedelta(hours=expiration_hours)
        signed_url = blob.generate_signed_url(expiration=expiration, method=method)
        return signed_url


# Singleton instance for convenience
signed_url_service = SignedUrlService()
