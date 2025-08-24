"""
URL configuration for dream_journal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView


def health_check(request: HttpRequest) -> JsonResponse:
    """Simple health check endpoint for Kubernetes probes"""
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    # JWT token endpoints
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include("dreams.urls")),  # dreams.urls already has api/ prefix
]
