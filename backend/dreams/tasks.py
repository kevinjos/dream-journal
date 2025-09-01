import base64
import logging
import os
from typing import Any

from celery import Task, shared_task
from google import genai
from google.cloud import storage

from .models import Image

logger = logging.getLogger(__name__)

# Initialize clients once at module level (per worker instance)
# These will be reused across all tasks in this worker
_gemini_client = None
_storage_client = None


def get_gemini_client() -> genai.Client:
    """Get or create the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Initialized Gemini client")
    return _gemini_client


def get_storage_client() -> storage.Client:
    """Get or create the GCS storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
        logger.info("Initialized GCS storage client")
    return _storage_client


@shared_task(bind=True, max_retries=3)
def generate_dream_image(
    self: Task, image_id: int, source_image_id: int | None = None
) -> dict[str, Any]:
    """
    Celery task to generate or alter an image for a dream using Gemini API and upload to GCS.

    Args:
        image_id: The ID of the Image record to generate
        source_image_id: Optional ID of source image for alterations

    Returns:
        dict containing task status and result information
    """
    try:
        image = Image.objects.get(id=image_id)

        if image.generation_status != Image.GenerationStatus.PENDING:
            logger.warning(
                f"Image {image_id} is not in PENDING status, skipping generation"
            )
            return {
                "status": "skipped",
                "reason": f"Image status is {image.generation_status}",
            }

        # Update status to generating
        image.generation_status = Image.GenerationStatus.GENERATING
        image.save()

        # Prepare content for Gemini API
        contents = []

        # Handle source image for alterations
        if source_image_id:
            logger.info(
                f"Getting image to alter for image {image_id} from source {source_image_id}"
            )

            try:
                source_image = Image.objects.get(id=source_image_id)
                if source_image.generation_status != Image.GenerationStatus.COMPLETED:
                    raise ValueError(f"Source image {source_image_id} is not completed")

                # Download source image from GCS
                bucket_name = os.environ.get("GCS_BUCKET_NAME", "dream-journal-images")
                storage_client = get_storage_client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(source_image.gcs_path)

                # Download image data
                source_image_bytes = blob.download_as_bytes()
                source_image_base64 = base64.b64encode(source_image_bytes).decode(
                    "utf-8"
                )

                # Add image to contents
                contents.append(
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": source_image_base64,
                        }
                    }
                )

            except Image.DoesNotExist as exc:
                raise ValueError(f"Source image {source_image_id} not found") from exc
            except Exception as exc:
                raise ValueError(f"Failed to download source image: {exc}") from exc

        logger.info(f"Starting image generation for image {image_id}")

        # Add text prompt to contents
        contents.append(image.generation_prompt)

        # Get singleton Gemini client
        gemini_client = get_gemini_client()

        # Call Gemini 2.5 Flash Image API
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents,
        )

        # Extract generated image data
        if not response.candidates or len(response.candidates) == 0:
            raise ValueError("No candidates in Gemini response")

        candidate = response.candidates[0]
        image_data = None

        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_data = part.inline_data.data
                    break

        if not image_data:
            raise ValueError("No image data in Gemini response")

        # Upload to GCS
        bucket_name = os.environ.get("GCS_BUCKET_NAME", "dream-journal-images")
        storage_client = get_storage_client()
        bucket = storage_client.bucket(bucket_name)

        # Decode base64 if needed
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data

        # Upload to GCS
        blob = bucket.blob(image.gcs_path)
        blob.upload_from_string(image_bytes, content_type="image/png")

        # Update image status to completed
        image.generation_status = Image.GenerationStatus.COMPLETED
        image.save()

        logger.info(f"Image generation completed successfully for image {image_id}")
        return {
            "status": "completed",
            "image_id": image_id,
        }

    except Image.DoesNotExist:
        logger.error(f"Image {image_id} does not exist")
        return {"status": "error", "error": f"Image {image_id} does not exist"}

    except Exception as exc:
        logger.error(
            f"Unexpected error in image generation task for image {image_id}: {exc}"
        )

        # Update image status to failed
        try:
            image = Image.objects.get(id=image_id)
            image.generation_status = Image.GenerationStatus.FAILED
            image.save()
        except Image.DoesNotExist:
            pass

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying image generation task for image {image_id} (attempt {self.request.retries + 1})"
            )
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc

        return {"status": "error", "error": str(exc)}
