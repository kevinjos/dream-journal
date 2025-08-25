from dj_rest_auth.registration.views import RegisterView
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


class CustomRegisterView(RegisterView):
    """
    Custom registration view that handles email verification properly.
    Returns appropriate response when email verification is mandatory.
    """

    def create(self, request: Request, *args, **kwargs) -> Response:
        # Check if email verification is mandatory before processing
        if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", None) == "mandatory":
            # Process registration but don't return JWT tokens
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # Return email verification message instead of user data
            return Response(
                {
                    "detail": "Verification e-mail sent. Please check your email and click the verification link to complete registration."
                },
                status=status.HTTP_201_CREATED,
            )

        # Normal registration flow for non-email-verification setups
        return super().create(request, *args, **kwargs)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request: Request) -> Response:
    """
    API endpoint to handle email verification from frontend.
    Expects a 'key' parameter in the request data.
    """
    import re

    key = request.data.get("key")
    if not key:
        return Response(
            {"detail": "Verification key is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Sanitize the verification key - allow only alphanumeric, hyphens, and underscores
    # This covers both regular keys and HMAC keys from allauth
    key = str(key).strip()
    if not re.match(r"^[a-zA-Z0-9_-]+$", key):
        return Response(
            {"detail": "Invalid verification key format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Additional length check to prevent excessive input
    if len(key) > 200:
        return Response(
            {"detail": "Invalid verification key format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Use allauth's method to handle different confirmation types (HMAC vs regular)
        from allauth.account.models import get_emailconfirmation_model

        EmailConfirmationModel = get_emailconfirmation_model()
        confirmation = EmailConfirmationModel.from_key(key)

        if confirmation is None:
            return Response(
                {
                    "detail": "Invalid or expired verification link. Please request a new verification link."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirm the email address
        email_address = confirmation.confirm(request)
        if email_address:
            return Response(
                {
                    "detail": "Email successfully verified! You can now log in to your account."
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "detail": "Email verification failed. The link may have expired. Please request a new verification link."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except (ValueError, TypeError) as e:
        # Handle invalid key format or type errors
        import logging

        logger = logging.getLogger("authentication.security")
        logger.warning(f"Invalid email verification key format: {str(e)[:100]}")
        return Response(
            {
                "detail": "Invalid verification link format. Please check your email or request a new verification link."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ImportError as e:
        # Handle import errors (shouldn't happen in production)
        import logging

        logger = logging.getLogger("authentication.security")
        logger.error(f"Import error in email verification: {e!s}")
        return Response(
            {
                "detail": "System error during email verification. Please try again later."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_email_verification(request: Request) -> Response:
    """
    API endpoint to resend email verification for a user.
    Expects 'email' in the request data.
    """
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    email = request.data.get("email")
    if not email:
        return Response(
            {"detail": "Email address is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Sanitize and validate email
    email = str(email).strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {"detail": "Invalid email address format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Additional length check
    if len(email) > 254:  # RFC 5321 maximum email length
        return Response(
            {"detail": "Invalid email address format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(email=email)

        # Get the primary email address
        email_address = EmailAddress.objects.filter(user=user, email=email).first()
        if not email_address:
            # Create EmailAddress record if it doesn't exist
            email_address = EmailAddress.objects.create(
                user=user, email=email, primary=True
            )

        # Check if email is already verified
        if email_address.verified:
            return Response(
                {"detail": "Email address is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send verification email
        email_address.send_confirmation(request, signup=False)

        return Response(
            {
                "detail": "Verification email sent successfully. Please check your email."
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        # Don't reveal if user exists or not for security
        return Response(
            {
                "detail": "If this email is registered, a verification link has been sent."
            },
            status=status.HTTP_200_OK,
        )
