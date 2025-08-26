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

from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.urls import include, path

from authentication.views import (
    CustomRegisterView,
    resend_email_verification,
    verify_email,
)


def health_check(request: HttpRequest) -> JsonResponse:
    """Simple health check endpoint for Kubernetes probes"""
    return JsonResponse({"status": "healthy"})


def password_reset_redirect(
    request: HttpRequest, uidb64: str, token: str
) -> HttpResponseRedirect:
    """Redirect password reset confirm to frontend"""
    frontend_url = (
        f"{settings.FRONTEND_DOMAIN}/#/auth/password-reset/confirm/{uidb64}/{token}/"
    )
    return HttpResponseRedirect(frontend_url)


def email_verification_redirect(request: HttpRequest, key: str) -> HttpResponseRedirect:
    """Redirect email verification to frontend"""
    frontend_url = (
        f"{settings.FRONTEND_DOMAIN}/#/auth/email-verification/confirm/{key}/"
    )
    return HttpResponseRedirect(frontend_url)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("api/auth/", include("dj_rest_auth.urls")),
    # Custom registration endpoint (MUST come after dj_rest_auth to override)
    path("api/auth/registration/", CustomRegisterView.as_view(), name="rest_register"),
    # Email verification endpoint
    path("api/auth/registration/verify-email/", verify_email, name="rest_verify_email"),
    # Resend email verification endpoint
    path(
        "api/auth/registration/resend-email/",
        resend_email_verification,
        name="rest_resend_email",
    ),
    # Custom redirect views - MUST come before allauth URLs to take precedence
    path(
        "api/accounts/confirm-email/<key>/",
        email_verification_redirect,
        name="account_confirm_email",
    ),
    path(
        "api/password-reset/confirm/<uidb64>/<token>/",
        password_reset_redirect,
        name="password_reset_confirm",
    ),
    # Minimal allauth URLs - only for URL pattern names that dj_rest_auth needs
    # We need some allauth URLs for the registration flow to work
    path("api/accounts/", include("allauth.urls")),
    path("api/", include("dreams.urls")),  # dreams.urls already has api/ prefix
]
