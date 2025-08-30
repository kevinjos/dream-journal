# GCP Project Module for Dream Journal
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Use existing Sensorium project
data "google_project" "sensorium" {
  project_id = var.project_id
}

locals {
  project_id = data.google_project.sensorium.project_id
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "dns.googleapis.com",
    "certificatemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "servicenetworking.googleapis.com",
    "iam.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudbilling.googleapis.com",
    "vpcaccess.googleapis.com"
  ])

  project = local.project_id
  service = each.key

  disable_on_destroy = false
}

# Default VPC Network
resource "google_compute_network" "main" {
  name                    = "dream-journal-vpc"
  project                 = local.project_id
  auto_create_subnetworks = false
  mtu                     = 1460

  depends_on = [google_project_service.apis]
}

# Subnet for the application
resource "google_compute_subnetwork" "app_subnet" {
  name          = "dream-journal-subnet"
  project       = local.project_id
  region        = var.region
  network       = google_compute_network.main.id
  ip_cidr_range = "10.0.0.0/24"
}



# VPC Connector for Cloud Run to access Cloud SQL
resource "google_vpc_access_connector" "cloud_run_connector" {
  name          = "dream-journal-connector"
  project       = local.project_id
  region        = var.region
  network       = google_compute_network.main.name
  ip_cidr_range = "10.8.0.0/28"
  max_instances = 10
  min_instances = 2

  depends_on = [google_project_service.apis]
}

# Service account for Cloud Run services
resource "google_service_account" "app_service_account" {
  account_id   = "cloud-run-app"
  project      = local.project_id
  display_name = "Cloud Run Application Service Account"
}

# Grant Secret Manager access to Cloud Run service account
resource "google_secret_manager_secret_iam_binding" "cloud_run_secret_access" {
  for_each = toset([
    google_secret_manager_secret.django_secret_key.secret_id,
    google_secret_manager_secret.db_url.secret_id,
    google_secret_manager_secret.sendgrid_api_key.secret_id
  ])

  project   = local.project_id
  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_service_account.email}",
  ]
}




# Cloud Build service account permissions
data "google_project" "project" {
  project_id = local.project_id
}

# Cloud Build service account uses default format when API is enabled
# Format: PROJECT_NUMBER@cloudbuild.gserviceaccount.com

# Grant Cloud Build access to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "cloudbuild_artifact_registry" {
  project    = local.project_id
  location   = google_artifact_registry_repository.docker_repo.location
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Grant Cloud Build access to Cloud Run
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = local.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Grant Cloud Build access to service account impersonation
resource "google_project_iam_member" "cloudbuild_service_account_user" {
  project = local.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Grant Cloud Build access to Secret Manager
resource "google_project_iam_member" "cloudbuild_secret_manager" {
  project = local.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Grant Cloud Build IAM permissions to manage secret and service account policies
resource "google_project_iam_member" "cloudbuild_iam_security_admin" {
  project = local.project_id
  role    = "roles/iam.securityAdmin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "postgres" {
  name             = "dream-journal-postgres"
  project          = local.project_id
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_tier

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled       = false
      private_network    = google_compute_network.main.id
      ssl_mode          = "ENCRYPTED_ONLY"
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    # Security: Enable database auditing (log statements)
    database_flags {
      name  = "log_statement"
      value = "all"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "0"
    }

    # Security: Password policy enforcement
    password_validation_policy {
      min_length                  = 12
      complexity                 = "COMPLEXITY_DEFAULT"
      reuse_interval            = 5
      disallow_username_substring = true
      enable_password_policy     = true
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }
  }

  deletion_protection = var.environment == "prod" ? true : false

  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Database for the application
resource "google_sql_database" "dream_journal_db" {
  name     = "dreamjournal"
  project  = local.project_id
  instance = google_sql_database_instance.postgres.name
}

# Generate a random password for the database user
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store database credentials in Secret Manager
resource "google_secret_manager_secret" "db_username" {
  secret_id = "db-username"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_username" {
  secret      = google_secret_manager_secret.db_username.id
  secret_data = "dreamjournal"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Store database connection string in Secret Manager
resource "google_secret_manager_secret" "db_url" {
  secret_id = "database-url"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret      = google_secret_manager_secret.db_url.id
  secret_data = "postgresql://dreamjournal:${urlencode(random_password.db_password.result)}@${google_sql_database_instance.postgres.private_ip_address}:5432/dreamjournal"
}

# Generate Django secret key
resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

# Store Django secret key in Secret Manager
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "django-secret-key"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "django_secret_key" {
  secret      = google_secret_manager_secret.django_secret_key.id
  secret_data = random_password.django_secret_key.result
}

# Generate Django admin password
resource "random_password" "django_admin_password" {
  length  = 20
  special = true
}

# Store Django admin password in Secret Manager
resource "google_secret_manager_secret" "django_admin_password" {
  secret_id = "django-admin-password"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "django_admin_password" {
  secret      = google_secret_manager_secret.django_admin_password.id
  secret_data = random_password.django_admin_password.result
}

# SendGrid API Key Secret
resource "google_secret_manager_secret" "sendgrid_api_key" {
  secret_id = "sendgrid-api-key"
  project   = local.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# Note: The actual SendGrid API key value should be added manually via console or CLI
# for security reasons. Run this command after terraform apply:
# echo -n "YOUR_SENDGRID_API_KEY" | gcloud secrets versions add sendgrid-api-key --data-file=-

# Artifact Registry for container images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  project       = local.project_id
  repository_id = "dream-journal"
  description   = "Docker repository for Dream Journal application"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}


# Cloud Run Domain Mappings
resource "google_cloud_run_domain_mapping" "frontend_domain" {
  location = var.region
  name     = "sensorium.dev"

  metadata {
    namespace = local.project_id
  }

  spec {
    route_name = "dream-journal-frontend"
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_domain_mapping" "backend_domain" {
  location = var.region
  name     = "api.sensorium.dev"

  metadata {
    namespace = local.project_id
  }

  spec {
    route_name = "dream-journal-backend"
  }

  depends_on = [google_project_service.apis]
}

# Cloud DNS managed zone (assuming it exists from Cloud Domains setup)
data "google_dns_managed_zone" "sensorium_dev" {
  name    = "sensorium-dev"
  project = local.project_id
}

# DNS CNAME records for Cloud Run domain mappings
resource "google_dns_record_set" "sensorium_dev_cname" {
  name         = data.google_dns_managed_zone.sensorium_dev.dns_name
  managed_zone = data.google_dns_managed_zone.sensorium_dev.name
  type         = "CNAME"
  ttl          = 300
  project      = local.project_id

  rrdatas = ["ghs.googlehosted.com."]

  depends_on = [google_cloud_run_domain_mapping.frontend_domain]
}

resource "google_dns_record_set" "api_sensorium_dev_cname" {
  name         = "api.${data.google_dns_managed_zone.sensorium_dev.dns_name}"
  managed_zone = data.google_dns_managed_zone.sensorium_dev.name
  type         = "CNAME"
  ttl          = 300
  project      = local.project_id

  rrdatas = ["ghs.googlehosted.com."]

  depends_on = [google_cloud_run_domain_mapping.backend_domain]
}

# Cloud Build Triggers
# Service account for Cloud Build triggers
resource "google_service_account" "cloudbuild_trigger_sa" {
  account_id   = "cloudbuild-trigger-sa"
  project      = local.project_id
  display_name = "Cloud Build Trigger Service Account"
  description  = "Service account for Cloud Build triggers"
}

# Grant necessary permissions to trigger service account
resource "google_project_iam_member" "cloudbuild_trigger_sa_permissions" {
  for_each = toset([
    "roles/cloudbuild.builds.editor",
    "roles/source.reader",
    "roles/logging.logWriter",
    "roles/editor"  # Broad permissions needed for infrastructure management
  ])

  project = local.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloudbuild_trigger_sa.email}"
}

# Grant Artifact Registry access to trigger service account
resource "google_artifact_registry_repository_iam_member" "cloudbuild_trigger_artifact_registry" {
  project    = local.project_id
  location   = google_artifact_registry_repository.docker_repo.location
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.cloudbuild_trigger_sa.email}"
}

# Grant specific bucket access for Terraform state
resource "google_storage_bucket_iam_member" "terraform_state_bucket_access" {
  bucket = "sensorium-terraform-state"
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloudbuild_trigger_sa.email}"
}

# Keep the repository resource for reference
resource "google_cloudbuildv2_repository" "dream_journal_repo" {
  project           = local.project_id
  location          = "us-central1"
  name              = "dream-journal"
  parent_connection = "projects/${local.project_id}/locations/us-central1/connections/github-kevinjos"
  remote_uri        = "https://github.com/kevinjos/dream-journal.git"
}

# Note: Cloud Build triggers are managed manually via Cloud Console due to Terraform provider
# limitations with 2nd generation repository connections. The triggers use the service account
# and permissions defined above.

# Database user
resource "google_sql_user" "dream_journal_user" {
  name     = "dreamjournal"
  project  = local.project_id
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  project       = local.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Log-based metric for new user registrations
resource "google_logging_metric" "new_user_registrations" {
  name   = "new_user_registrations"
  project = local.project_id

  filter = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="dream-journal-backend"
    jsonPayload.name="django.security"
    jsonPayload.message=~"User .* registered successfully"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    display_name = "New User Registrations"

    labels {
      key         = "username"
      value_type  = "STRING"
      description = "Username of the registered user"
    }
  }

  label_extractors = {
    "username" = "EXTRACT(jsonPayload.message)"
  }

  depends_on = [google_project_service.apis]
}

# Notification channel for alerts (email)
resource "google_monitoring_notification_channel" "email_alerts" {
  display_name = "Dream Journal Email Alerts"
  project      = local.project_id
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  depends_on = [google_project_service.apis]
}

# Alert policy for new user registrations
resource "google_monitoring_alert_policy" "new_user_alert" {
  display_name = "New User Registration Alert"
  project      = local.project_id
  combiner     = "OR"
  enabled      = true

  conditions {
    display_name = "New user registration detected"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/user/${google_logging_metric.new_user_registrations.name}\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.email_alerts.name
  ]

  depends_on = [
    google_project_service.apis,
    google_logging_metric.new_user_registrations
  ]
}
