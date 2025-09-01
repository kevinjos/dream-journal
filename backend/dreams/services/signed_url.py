"""Service for generating signed URLs for Google Cloud Storage."""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from google.cloud import storage

from dreams.models import Image

logger = logging.getLogger(__name__)


class SignedUrlService:
    """Service for generating signed URLs for GCS access."""

    def __init__(self) -> None:
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.service_account_path = getattr(settings, "SERVICE_ACCOUNT_PATH", None)
        self.service_account_email = getattr(
            settings, "GCS_SERVICE_ACCOUNT_EMAIL", None
        )

        if self.service_account_path:
            # Use service account JSON key (has private key for signing)
            self.storage_client = storage.Client.from_service_account_json(
                str(self.service_account_path)
            )
        else:
            # Use default credentials with IAM-based signing
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
        expiration = timezone.now() + timedelta(hours=expiration_hours)

        if self.service_account_path:
            # Use key-based signing for local development with service account JSON
            signed_url = blob.generate_signed_url(expiration=expiration, method=method)
        else:
            # Use IAM-based signing for Cloud Run (requires iam.serviceAccountTokenCreator role)
            # Must explicitly provide service account email for Compute Engine credentials
            signed_url = blob.generate_signed_url(
                expiration=expiration,
                method=method,
                version="v4",
                service_account_email=self.service_account_email,
            )

        return signed_url


# Singleton instance for convenience
signed_url_service = SignedUrlService()
