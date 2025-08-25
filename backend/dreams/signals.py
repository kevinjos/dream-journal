from django.db import models
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from .models import Dream, Quality


@receiver(m2m_changed, sender=Dream.qualities.through)  # type: ignore[misc]
def update_quality_frequencies_and_cleanup(
    sender: type[models.Model],
    instance: Dream,
    action: str,
    pk_set: set[int] | None,
    **kwargs: dict[str, object],
) -> None:
    """
    Update quality frequencies and clean up orphaned qualities.
    Triggered when the many-to-many relationship between Dream and Quality changes.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        # Update frequencies for affected qualities
        if action == "post_clear":
            # If clearing, update all qualities for this user
            qualities = Quality.objects.filter(user=instance.user)
            for quality in qualities:
                quality.update_frequency()
        elif pk_set:
            # Update the changed qualities
            qualities = Quality.objects.filter(pk__in=pk_set)
            for quality in qualities:
                quality.update_frequency()

    if action == "post_remove" and pk_set:
        # Check which qualities became orphaned (frequency = 0)
        orphaned_qualities = Quality.objects.filter(pk__in=pk_set, frequency=0)
        orphaned_qualities.delete()


@receiver(post_delete, sender=Dream)  # type: ignore[misc]
def cleanup_qualities_after_dream_deletion(
    sender: type[models.Model], instance: Dream, **kwargs: dict[str, object]
) -> None:
    """
    Update frequencies and clean up orphaned qualities after a dream is deleted.
    """
    # Get qualities that were associated with this dream before deletion
    # Note: The M2M relationship is already cleared by Django before post_delete
    # So we need to update all user qualities
    user_qualities = Quality.objects.filter(user=instance.user)

    for quality in user_qualities:
        quality.update_frequency()

    # Delete qualities with frequency = 0
    user_qualities.filter(frequency=0).delete()
