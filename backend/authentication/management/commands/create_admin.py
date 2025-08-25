"""
Management command to create a superuser if none exists.
Safe to run multiple times - only creates if no superuser exists.
"""

import logging
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser if none exists"

    def handle(self, *args, **options) -> None:  # type: ignore[override]
        # Check if any superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS("Superuser already exists, skipping creation.")
            )
            return

        # Get admin credentials from environment variables
        admin_username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        admin_email = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@sensorium.dev")
        admin_password = os.environ.get("DJANGO_ADMIN_PASSWORD")

        if not admin_password:
            self.stdout.write(
                self.style.ERROR(
                    "DJANGO_ADMIN_PASSWORD environment variable is required"
                )
            )
            return

        try:
            # Create the superuser
            User.objects.create_superuser(  # type: ignore[misc]
                username=admin_username, email=admin_email, password=admin_password
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created superuser: {admin_username}")
            )
            logger.info(f"Created superuser: {admin_username}")

        except IntegrityError as e:
            # Handle race condition where user was created between our check and create
            if "username" in str(e):
                self.stdout.write(
                    self.style.WARNING(f"Username {admin_username} already exists")
                )
            else:
                self.stdout.write(self.style.ERROR(f"Error creating superuser: {e}"))
                logger.error(f"Error creating superuser: {e}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Unexpected error creating superuser: {e}")
            )
            logger.error(f"Unexpected error creating superuser: {e}")
