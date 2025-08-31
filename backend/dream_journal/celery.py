import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dream_journal.settings")

app = Celery("dream_journal")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("celery_config", namespace="")

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
