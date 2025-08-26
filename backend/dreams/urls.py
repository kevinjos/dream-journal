from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .nested_views import DreamQualityViewSet
from .views import DreamViewSet, QualityViewSet

# Main router
router = DefaultRouter()
router.register(r"dreams", DreamViewSet, basename="dream")
router.register(r"qualities", QualityViewSet, basename="quality")

# Manual nested routes for now (can implement drf-nested-routers later)
nested_urlpatterns = [
    path(
        "dreams/<int:dream_pk>/qualities/",
        DreamQualityViewSet.as_view({"get": "list"}),
        name="dream-qualities-list",
    ),
    path(
        "dreams/<int:dream_pk>/qualities/<int:pk>/",
        DreamQualityViewSet.as_view({"put": "update", "delete": "destroy"}),
        name="dream-qualities-detail",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
    path("", include(nested_urlpatterns)),
]
