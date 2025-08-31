variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run worker service"
  type        = string
  default     = "dream-journal-celery-worker"
}

variable "image_url" {
  description = "Container image URL for the Celery worker"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key for image generation"
  type        = string
  sensitive   = true
}

variable "gcs_bucket_name" {
  description = "GCS bucket name for image storage"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of worker instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of worker instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for each worker instance"
  type        = string
  default     = "1000m"
}

variable "memory_limit" {
  description = "Memory limit for each worker instance"
  type        = string
  default     = "1Gi"
}

variable "vpc_connector_name" {
  description = "VPC connector name for Pub/Sub access"
  type        = string
}

# Cloud Run service for Celery worker
resource "google_cloud_run_v2_service" "celery_worker" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    # Scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # VPC access for Pub/Sub
    vpc_access {
      connector = var.vpc_connector_name
      egress    = "ALL_TRAFFIC"
    }

    containers {
      name  = "celery-worker"
      image = var.image_url

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle                = true
        startup_cpu_boost       = true
      }

      # Environment variables
      env {
        name  = "DJANGO_SETTINGS_MODULE"
        value = "dream_journal.settings"
      }

      env {
        name  = "DEBUG"
        value = "False"
      }

      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }

      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = var.gcs_bucket_name
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "CELERY_BROKER_URL"
        value = "gcpubsub://"
      }

      # Startup and liveness probes
      startup_probe {
        initial_delay_seconds = 60
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3

        exec {
          command = ["celery", "-A", "dream_journal", "inspect", "ping", "--destination=celery@${var.service_name}"]
        }
      }

      liveness_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 10
        period_seconds        = 30
        failure_threshold     = 3

        exec {
          command = ["celery", "-A", "dream_journal", "inspect", "ping", "--destination=celery@${var.service_name}"]
        }
      }
    }

    # Service account for worker
    service_account = google_service_account.celery_worker.email

    # Worker-specific annotations
    annotations = {
      "autoscaling.knative.dev/minScale"           = var.min_instances
      "autoscaling.knative.dev/maxScale"           = var.max_instances
      "run.googleapis.com/execution-environment"   = "gen2"
      "run.googleapis.com/cpu-throttling"          = "false"
    }
  }

  # Traffic configuration
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_service_account.celery_worker,
    google_project_iam_member.celery_worker_pubsub,
    google_project_iam_member.celery_worker_storage,
    google_project_iam_member.celery_worker_sql,
    google_pubsub_topic.celery_topic,
    google_pubsub_subscription.celery_subscription
  ]
}

# Service account for the Celery worker
resource "google_service_account" "celery_worker" {
  account_id   = "${var.service_name}-sa"
  display_name = "Celery Worker Service Account"
  project      = var.project_id
}

# IAM permissions for Pub/Sub
resource "google_project_iam_member" "celery_worker_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.celery_worker.email}"
}

# IAM permissions for Cloud Storage
resource "google_project_iam_member" "celery_worker_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.celery_worker.email}"
}

# IAM permissions for Cloud SQL (if using Cloud SQL)
resource "google_project_iam_member" "celery_worker_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.celery_worker.email}"
}

# Pub/Sub topic for Celery messages
resource "google_pubsub_topic" "celery_topic" {
  name    = "celery-topic"
  project = var.project_id

  message_retention_duration = "86400s" # 24 hours
}

# Pub/Sub subscription for Celery workers
resource "google_pubsub_subscription" "celery_subscription" {
  name    = "celery-subscription"
  topic   = google_pubsub_topic.celery_topic.name
  project = var.project_id

  # Message delivery settings
  ack_deadline_seconds       = 600  # 10 minutes for long-running tasks
  message_retention_duration = "86400s" # 24 hours
  retain_acked_messages      = false

  # Retry policy for failed messages
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s" # 5 minutes
  }

  # Dead letter policy for permanently failed messages
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.celery_dead_letter.id
    max_delivery_attempts = 5
  }

  depends_on = [google_pubsub_topic.celery_dead_letter]
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "celery_dead_letter" {
  name    = "celery-dead-letter"
  project = var.project_id

  message_retention_duration = "604800s" # 7 days
}

# Outputs
output "service_url" {
  description = "URL of the Cloud Run worker service"
  value       = google_cloud_run_v2_service.celery_worker.uri
}

output "service_name" {
  description = "Name of the Cloud Run worker service"
  value       = google_cloud_run_v2_service.celery_worker.name
}

output "service_account_email" {
  description = "Email of the service account used by the worker"
  value       = google_service_account.celery_worker.email
}

output "pubsub_topic" {
  description = "Pub/Sub topic name for Celery"
  value       = google_pubsub_topic.celery_topic.name
}

output "pubsub_subscription" {
  description = "Pub/Sub subscription name for Celery"
  value       = google_pubsub_subscription.celery_subscription.name
}
