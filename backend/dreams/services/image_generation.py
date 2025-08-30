import os
import uuid
from datetime import datetime, timedelta

from django.utils import timezone
from google.cloud import aiplatform, storage

from dreams.models import Dream, Image


class ImageGenerationService:
    """Service for generating and managing dream images using Vertex AI and GCS."""

    def __init__(self) -> None:
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "dream-journal-dev")
        self.location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "dream-journal-images")

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Initialize GCS client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def generate_image_for_dream(
        self, dream: Dream, custom_prompt: str | None = None
    ) -> Image:
        """
        Generate an image for a dream using Vertex AI Imagen.

        Args:
            dream: The Dream instance to generate an image for
            custom_prompt: Optional custom prompt, otherwise uses dream description

        Returns:
            Image instance with pending status
        """
        # Create the prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Use dream description as base prompt, with some artistic enhancement
            prompt = f"A dreamlike, surreal artistic interpretation of: {dream.description[:500]}"

        # Generate unique GCS path
        image_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gcs_path = (
            f"users/{dream.user.id}/dreams/{dream.id}/images/{image_id}_{timestamp}.png"
        )

        # Create Image record
        dream_image = Image.objects.create(
            dream=dream,
            gcs_path=gcs_path,
            generation_prompt=prompt,
            generation_status=Image.GenerationStatus.PENDING,
        )

        # Trigger async image generation
        self._generate_image_async(dream_image)

        return dream_image

    def _generate_image_async(self, dream_image: Image) -> None:
        """
        Generate image using Vertex AI Imagen API.
        In production, this should be run as a background task.
        """
        try:
            # Update status to generating
            dream_image.generation_status = Image.GenerationStatus.GENERATING
            dream_image.save(update_fields=["generation_status"])

            # Configure Imagen parameters
            endpoint_name = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/imagen-3.0-generate-001"

            # Prepare the request
            instances = [
                {
                    "prompt": dream_image.generation_prompt,
                }
            ]

            parameters = {
                "sampleCount": 1,
                "aspectRatio": "1:1",  # Square images
                "safetyFilterLevel": "block_some",
                "personGeneration": "dont_allow",  # Avoid generating people for privacy
            }

            # Call Vertex AI Imagen
            endpoint = aiplatform.Endpoint(endpoint_name)
            response = endpoint.predict(instances=instances, parameters=parameters)

            # Extract generated image data
            if response.predictions and len(response.predictions) > 0:
                prediction = response.predictions[0]

                # The response contains base64-encoded image data
                image_data = prediction.get("bytesBase64Encoded")
                if image_data:
                    # Upload to GCS
                    self._upload_to_gcs(dream_image, image_data)

                    # Update status to completed
                    dream_image.generation_status = Image.GenerationStatus.COMPLETED
                    dream_image.save(update_fields=["generation_status"])
                else:
                    raise ValueError("No image data in response")
            else:
                raise ValueError("No predictions in response")

        except Exception as e:
            # Mark as failed
            dream_image.generation_status = Image.GenerationStatus.FAILED
            dream_image.save(update_fields=["generation_status"])

            # Log the error (in production, use proper logging)
            print(f"Image generation failed for Image {dream_image.id}: {e!s}")

    def _upload_to_gcs(self, dream_image: Image, image_data: str) -> None:
        """Upload base64-encoded image data to Google Cloud Storage."""
        import base64

        # Decode base64 image data
        image_bytes = base64.b64decode(image_data)

        # Create blob and upload
        blob = self.bucket.blob(dream_image.gcs_path)
        blob.upload_from_string(image_bytes, content_type="image/png")

    def get_signed_url(self, dream_image: Image) -> str:
        """
        Get a signed URL for accessing the image.
        Always generates a fresh URL with 1-hour expiration.
        """
        # Generate new signed URL (1 hour expiration)
        blob = self.bucket.blob(dream_image.gcs_path)
        signed_url = blob.generate_signed_url(
            expiration=timezone.now() + timedelta(hours=1), method="GET"
        )

        return signed_url

    def delete_image(self, dream_image: Image) -> None:
        """Delete image from both GCS and database."""
        try:
            # Delete from GCS
            blob = self.bucket.blob(dream_image.gcs_path)
            blob.delete()
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Failed to delete GCS file {dream_image.gcs_path}: {e!s}")

        # Delete from database
        dream_image.delete()


# Singleton instance
image_service = ImageGenerationService()
