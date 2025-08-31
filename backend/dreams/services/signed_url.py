"""Service for generating signed URLs for Google Cloud Storage."""

import logging
import os
from datetime import timedelta

from django.utils import timezone
from google.cloud import storage

from dreams.models import Image

logger = logging.getLogger(__name__)


class SignedUrlService:
    """Service for generating signed URLs for GCS access."""

    def __init__(self) -> None:
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "dream-journal-images")
        service_account_path = os.environ.get("SERVICE_ACCOUNT_PATH")

        if service_account_path:
            self.storage_client = storage.Client.from_service_account_json(
                str(service_account_path)
            )
        else:
            self.storage_client = storage.Client()

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
        signed_url = blob.generate_signed_url(
            expiration=timezone.now() + timedelta(hours=expiration_hours), method=method
        )
        return signed_url


# Singleton instance for convenience
signed_url_service = SignedUrlService()
