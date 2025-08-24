from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DreamViewSet, QualityViewSet
from .nested_views import DreamQualityViewSet

# Main router
router = DefaultRouter()
router.register(r'dreams', DreamViewSet, basename='dream')
router.register(r'qualities', QualityViewSet, basename='quality')

# Manual nested routes for now (can implement drf-nested-routers later)
nested_urlpatterns = [
    path('dreams/<int:dream_pk>/qualities/', 
         DreamQualityViewSet.as_view({'get': 'list'}), 
         name='dream-qualities-list'),
    path('dreams/<int:dream_pk>/qualities/<int:pk>/', 
         DreamQualityViewSet.as_view({'put': 'update', 'delete': 'destroy'}), 
         name='dream-qualities-detail'),
]

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(nested_urlpatterns)),
]