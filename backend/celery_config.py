import os

from django.conf import settings

broker_url = (
    "redis://localhost:9003/0"
    if settings.DEBUG
    else f'gcpubsub://projects/{os.getenv("GOOGLE_CLOUD_PROJECT")}'
)

broker_transport_options = (
    {
        "region": "us-central1",
        "is_async": True,
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "ack_deadline_seconds": 60,
    }
    if not settings.DEBUG
    else {}
)

result_backend = "django-db"
result_cache_max_age = 3600

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000
