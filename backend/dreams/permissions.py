from django.db import models
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view/edit it.
    Assumes the model has a 'user' field that points to the owner.
    """

    def has_object_permission(
        self, request: Request, view: ViewSet, obj: models.Model
    ) -> bool:
        """
        Check if the requesting user owns the object.
        Returns 404 (not 403) to prevent information leakage about object existence.
        """
        # Check if the object has a user attribute and it matches the request user
        return hasattr(obj, "user") and obj.user == request.user


class IsAuthenticatedAndOwner(permissions.BasePermission):
    """
    Combines authentication check with ownership check.
    This ensures users must be logged in AND own the object.
    """

    def has_permission(self, request: Request, view: ViewSet) -> bool:
        """Check if user is authenticated for all operations."""
        return request.user and request.user.is_authenticated

    def has_object_permission(
        self, request: Request, view: ViewSet, obj: models.Model
    ) -> bool:
        """Check if the authenticated user owns the object."""
        return hasattr(obj, "user") and obj.user == request.user
