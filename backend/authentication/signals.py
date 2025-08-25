import logging

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed, user_signed_up
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.http import HttpRequest

# Security logging for monitoring
security_logger = logging.getLogger("django.security")


@receiver(user_signed_up)
def log_user_registration(
    sender: type[User],
    request: HttpRequest,
    user: User | None,
    **kwargs: dict[str, object],
) -> None:
    """
    Log new user registrations to django.security logger for GCP monitoring.
    This signal fires when a user successfully registers via allauth/dj-rest-auth.
    Note: user might be None if email verification is mandatory and handled by custom serializer.
    """
    # Handle case where user might be None due to email verification requirements
    if user is None:
        return

    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")[
        :100
    ]  # Truncate long user agents

    security_logger.info(
        f"User {user.username} registered (email verification pending) from IP {ip_address} "
        f"user_agent={user_agent} email={user.email}"
    )


@receiver(email_confirmed)
def log_email_verification(
    sender: type, request: HttpRequest, email_address: EmailAddress, **kwargs
) -> None:
    """
    Log email verification completions to django.security logger for GCP monitoring.
    This signal fires when a user successfully verifies their email address.
    """
    user = email_address.user
    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")[
        :100
    ]  # Truncate long user agents

    security_logger.info(
        f"User {user.username} verified email {email_address.email} from IP {ip_address} "
        f"user_agent={user_agent}"
    )
