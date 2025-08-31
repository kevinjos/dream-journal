import os

from django.conf import settings
from kombu import Queue

# Queue name constants
QUEUE_DEFAULT = "default"
QUEUE_IMAGE_GENERATION = "image_generation"

broker_url = (
    "redis://localhost:9003/0"
    if settings.DEBUG
    else f'gcpubsub://projects/{os.getenv("GOOGLE_CLOUD_PROJECT")}'
)

broker_transport_options = (
    {
        "region": "us-central1",
        "is_async": True,
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

task_routes = {
    "dreams.tasks.generate_dream_image": {"queue": QUEUE_IMAGE_GENERATION},
}

task_default_queue = QUEUE_DEFAULT
task_queues = (
    Queue(QUEUE_DEFAULT),
    Queue(QUEUE_IMAGE_GENERATION),
)

worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000

if not settings.DEBUG:
    broker_transport_options.update(
        {
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "subscription_name": "celery-subscription",
            "topic_name": "celery-topic",
        }
    )
