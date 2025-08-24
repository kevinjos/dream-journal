from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.viewsets import ViewSet


class HasUser(Protocol):
    """Protocol for objects that have a user attribute."""

    user: object


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view/edit it.
    Assumes the model has a 'user' field that points to the owner.
    """

    def has_object_permission(
        self, request: Request, _view: ViewSet, obj: HasUser
    ) -> bool:
        """
        Check if the requesting user owns the object.
        Returns 404 (not 403) to prevent information leakage about object existence.
        """
        # Check if the object's user matches the request user
        return obj.user == request.user


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
