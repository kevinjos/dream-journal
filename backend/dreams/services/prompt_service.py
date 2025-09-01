"""
Service for generating AI prompts for dream image generation and alteration.
"""

from dreams.models import Dream


class PromptService:
    """Service for generating prompts for dream image AI generation."""

    @staticmethod
    def generate_image_prompt(dream: Dream) -> str:
        """
        Generate a prompt for creating a new dream image.

        Args:
            dream: The Dream instance

        Returns:
            Formatted prompt for image generation
        """
        # Generate prompt with user-defined qualities and description
        qualities_list = ", ".join([q.name for q in dream.qualities.all()])
        qualities_text = (
            f"Qualities: {qualities_list}"
            if qualities_list
            else "No specific qualities"
        )

        return f"""Create an image of my dream with the following qualities and description:
{qualities_text}
Description: {dream.description}"""

    @staticmethod
    def generate_alteration_prompt(
        user_prompt: str, dream: Dream, dream_updated_since_image: bool = False
    ) -> str:
        """
        Generate a prompt for altering an existing dream image.

        Args:
            user_prompt: User's description of desired alterations
            dream: The Dream instance
            dream_updated_since_image: Whether the dream has been updated since the image was created

        Returns:
            Formatted prompt for image alteration following Gemini API docs
        """
        base_prompt = f"Using the image of my dream, please apply the following alterations: {user_prompt}"

        if dream_updated_since_image:
            qualities_list = ", ".join([q.name for q in dream.qualities.all()])
            base_prompt += f"\n\nNote: The dream has been updated since this image was created. Current state:\nQualities: {qualities_list}\nDescription: {dream.description}\nPlease blend these updates with the requested alterations."

        return base_prompt

    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """
        Validate that a prompt is suitable for image generation.

        Args:
            prompt: The prompt to validate

        Returns:
            True if prompt is valid, False otherwise
        """
        if not prompt or not prompt.strip():
            return False

        # Add any additional validation rules here
        # e.g., length limits, content filtering, etc.

        return True
