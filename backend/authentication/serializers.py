from typing import Any

from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework import serializers

User = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    """Custom login serializer that enforces email verification when mandatory."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Check if email verification is mandatory before parent validation
        from django.conf import settings
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", None) == "mandatory":
            # Get the user before parent validation to check email verification
            username = attrs.get("username")
            password = attrs.get("password")

            if username and password:
                try:
                    # Try to find the user (could be username or email depending on ACCOUNT_AUTHENTICATION_METHOD)
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    try:
                        # Try by email if username lookup failed
                        user = User.objects.get(email=username)
                    except User.DoesNotExist:
                        user = None

                if user:
                    # Check if user has a verified email address
                    verified_email_exists = EmailAddress.objects.filter(
                        user=user, verified=True
                    ).exists()

                    if not verified_email_exists:
                        # Check if password is correct before showing email verification error
                        from django.contrib.auth import authenticate

                        authenticated_user = authenticate(
                            username=username, password=password
                        )

                        if authenticated_user:
                            # User exists and password is correct, but email not verified
                            # Get user's primary email address
                            email_address = EmailAddress.objects.filter(
                                user=user, primary=True
                            ).first()
                            user_email = (
                                email_address.email
                                if email_address
                                else getattr(user, "email", username)
                            )

                            # Check if there's a recent verification email that hasn't expired
                            from datetime import timedelta

                            from allauth.account import app_settings
                            from allauth.account.models import EmailConfirmation
                            from django.utils import timezone

                            can_resend = True
                            if email_address:
                                recent_confirmation = EmailConfirmation.objects.filter(
                                    email_address=email_address,
                                    sent__gte=timezone.now()
                                    - timedelta(
                                        days=app_settings.EMAIL_CONFIRMATION_EXPIRE_DAYS
                                    ),
                                ).first()

                                if (
                                    recent_confirmation
                                    and not recent_confirmation.key_expired()
                                ):
                                    can_resend = False

                            # Return structured error for better frontend UX
                            error_data = {
                                "email_verification_required": True,
                                "detail": "Email verification required. Please check your email and click the verification link."
                                if not can_resend
                                else "Email verification required. You can resend the verification email.",
                                "can_resend": can_resend,
                                "email": user_email,
                            }

                            raise serializers.ValidationError(error_data)

        # If we get here, either email verification is not mandatory or user is verified
        # Run the parent validation
        return super().validate(attrs)


class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer that validates email addresses properly."""

    def validate_email(self, email: str) -> str:
        """Validate email during registration - check for existing accounts."""
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email

        User = get_user_model()

        # Sanitize and validate email format
        email = str(email).strip().lower()
        try:
            validate_email(email)
        except ValidationError as e:
            raise serializers.ValidationError("Invalid email address format.") from e

        # Additional length check
        if len(email) > 254:  # RFC 5321 maximum email length
            raise serializers.ValidationError("Email address is too long.")

        # Check if email verification is mandatory
        if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", None) == "mandatory":
            try:
                existing_user = User.objects.get(email=email)

                # Check if user has verified email
                verified_email_exists = EmailAddress.objects.filter(
                    user=existing_user, verified=True
                ).exists()

                if verified_email_exists:
                    # Use generic message to prevent user enumeration
                    raise serializers.ValidationError(
                        "Unable to register with this email address."
                    )
                else:
                    # Silently allow re-registration attempts for unverified emails
                    # The system will handle sending a new verification email
                    pass

            except User.DoesNotExist:
                # Email doesn't exist, registration can proceed
                pass

        return email

    def save(self, request: HttpRequest) -> User:  # type: ignore[override]
        # Call parent save to create user and send verification email
        user = super().save(request)
        return user
