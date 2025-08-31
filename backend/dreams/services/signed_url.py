"""Service for generating signed URLs for Google Cloud Storage."""

import logging
import os
from datetime import timedelta
from pathlib import Path

from django.utils import timezone
from google.cloud import storage

from dreams.models import Image

logger = logging.getLogger(__name__)


class SignedUrlService:
    """Service for generating signed URLs for GCS access."""

    def __init__(self) -> None:
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "dream-journal-images")

        # Use service account key for signed URL generation
        service_account_path = (
            Path.home() / ".gcloud-keys" / "dream-journal-cloud-run-app-key.json"
        )
        if service_account_path.exists():
            self.storage_client = storage.Client.from_service_account_json(
                str(service_account_path)
            )
            logger.info(f"Using service account key from {service_account_path}")
        else:
            # Fall back to default credentials (for development)
            self.storage_client = storage.Client()
            logger.warning(
                f"Service account key not found at {service_account_path}, using default credentials"
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
        signed_url = blob.generate_signed_url(
            expiration=timezone.now() + timedelta(hours=expiration_hours), method=method
        )
        return signed_url


# Singleton instance for convenience
signed_url_service = SignedUrlService()
