import logging

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def format_email_subject(self, subject: str) -> str:
        """
        Use configurable email subject prefix from settings.
        """
        from django.conf import settings

        # Use the allauth-specific email subject prefix from settings
        prefix = getattr(settings, "ACCOUNT_EMAIL_SUBJECT_PREFIX", "[sensorium.dev] ")
        formatted = prefix + subject
        logger.info(
            f"CustomAccountAdapter.format_email_subject: '{subject}' -> '{formatted}'"
        )
        return formatted
