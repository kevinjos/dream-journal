import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailConfirmation
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def format_email_subject(self, subject: str) -> str:
        """
        Use configurable email subject prefix from settings.
        """
        from django.conf import settings

        # Use the allauth-specific email subject prefix from settings
        prefix: str = getattr(
            settings, "ACCOUNT_EMAIL_SUBJECT_PREFIX", "[sensorium.dev] "
        )
        formatted: str = prefix + subject
        logger.info(
            f"CustomAccountAdapter.format_email_subject: '{subject}' -> '{formatted}'"
        )
        return formatted

    def get_email_confirmation_url(
        self, request: HttpRequest, emailconfirmation: EmailConfirmation
    ) -> str:
        """
        Override to prepend /api to the confirmation URL so it routes through our ingress correctly.
        """
        # Get the default URL from parent
        url: str = super().get_email_confirmation_url(request, emailconfirmation)

        # Replace the /accounts/ path with /api/accounts/
        # The default URL will be like: https://sensorium.dev/accounts/confirm-email/KEY/
        # We want: https://sensorium.dev/api/accounts/confirm-email/KEY/
        url = url.replace("/accounts/", "/api/accounts/")

        logger.info(f"Modified email confirmation URL: {url}")
        return url
