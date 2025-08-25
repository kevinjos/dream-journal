import logging
from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from django.core.mail import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def format_email_subject(self, subject: str) -> str:
        """
        Use configurable email subject prefix from settings.
        """
        from django.conf import settings

        # Use the allauth-specific email subject prefix from settings
        prefix = getattr(settings, "ACCOUNT_EMAIL_SUBJECT_PREFIX", "[Dream Journal] ")
        formatted = prefix + subject
        logger.info(
            f"CustomAccountAdapter.format_email_subject: '{subject}' -> '{formatted}'"
        )
        return formatted

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """
        Override send_mail to log the email details before sending.
        """
        logger.info(
            f"CustomAccountAdapter.send_mail called with template_prefix='{template_prefix}', email='{email}'"
        )

        # Call the parent method to do the actual work
        super().send_mail(template_prefix, email, context)

        logger.info("CustomAccountAdapter.send_mail completed")

    def render_mail(
        self,
        template_prefix: str,
        email: str,
        context: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> EmailMultiAlternatives | EmailMessage:
        """
        Override render_mail to log the exact subject being sent.
        """
        msg = super().render_mail(template_prefix, email, context, headers)
        logger.info(
            f"CustomAccountAdapter.render_mail: Final email subject = '{msg.subject}'"
        )
        return msg
