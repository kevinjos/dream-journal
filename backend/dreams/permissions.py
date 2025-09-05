from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.viewsets import ViewSet


class HasUser(Protocol):
    """Protocol for objects that have a user attribute."""

    user: object


class IsAuthenticatedAndOwner(permissions.BasePermission):
    """
    Combines authentication check with ownership check.
    This ensures users must be logged in AND own the object.
    """

    def has_permission(self, request: Request, _view: ViewSet) -> bool:
        """Check if user is authenticated for all operations."""
        return request.user and request.user.is_authenticated

    def has_object_permission(
        self, request: Request, _view: ViewSet, obj: HasUser
    ) -> bool:
        """Check if the authenticated user owns the object."""
        return obj.user == request.user


class IsAuthenticatedAndIsOwnerOrIsPublic(permissions.BasePermission):
    """
    Custom permission for dreams that can be public.
    - Owners have full access to their dreams
    - Authenticated users can read public dreams (anonymously)
    - Write operations restricted to owners only
    """

    def has_permission(self, request: Request, _view: ViewSet) -> bool:
        """Check if user is authenticated for all operations."""
        return request.user and request.user.is_authenticated

    def has_object_permission(
        self, request: Request, _view: ViewSet, obj: HasUser
    ) -> bool:
        """
        Check object-level permissions.
        - Read access: owner OR (public dream AND safe method)
        - Write access: owner only
        """
        # Owner has full access
        if obj.user == request.user:
            return True

        # For non-owners, only allow read access to public dreams
        if request.method in permissions.SAFE_METHODS:
            return getattr(obj, "is_public", False)

        return False
