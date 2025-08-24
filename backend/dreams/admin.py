from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Dream, Quality


@admin.register(Dream)
class DreamAdmin(admin.ModelAdmin):
    list_display = ("get_title", "user", "created", "updated")
    list_filter = ("created", "updated", "user")
    search_fields = ("description",)
    readonly_fields = ("created", "updated")
    filter_horizontal = ("qualities",)

    def get_title(self, obj: Dream) -> str:
        """Display first 50 characters of description as title"""
        if obj.description:
            return (
                obj.description[:50] + "..."
                if len(obj.description) > 50
                else obj.description
            )
        return "(No description)"

    get_title.short_description = "Title"  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Dream]:
        """Only show dreams for the current user - dreams are private"""
        qs = super().get_queryset(request)
        return qs.filter(user=request.user)


@admin.register(Quality)
class QualityAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "frequency", "created")
    list_filter = ("created", "user", "frequency")
    search_fields = ("name",)
    readonly_fields = ("frequency", "created")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Quality]:
        """Only show qualities for the current user - qualities are private"""
        qs = super().get_queryset(request)
        return qs.filter(user=request.user)
