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
    "container.googleapis.com",
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
    "cloudbilling.googleapis.com"
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

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# Cloud NAT for outbound internet access
resource "google_compute_router" "main" {
  name    = "dream-journal-router"
  project = local.project_id
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "main" {
  name   = "dream-journal-nat"
  project = local.project_id
  router = google_compute_router.main.name
  region = var.region

  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "dream-journal-allow-internal"
  project = local.project_id
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["dream-journal"]
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "dream-journal-allow-health-checks"
  project = local.project_id
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["8080", "8000", "9000"]
  }

  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16"
  ]
  target_tags = ["dream-journal"]
}

# GKE Autopilot Cluster
resource "google_container_cluster" "dream_journal" {
  name     = "dream-journal-autopilot"
  project  = local.project_id
  location = var.region

  # Enable Autopilot mode
  enable_autopilot = true

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.app_subnet.name

  # IP allocation for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Enable private nodes (no public IPs)
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "10.10.0.0/28"
  }

  # Master authorized networks (for kubectl access)
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }

  # Autopilot clusters automatically enable Workload Identity
  workload_identity_config {
    workload_pool = "${local.project_id}.svc.id.goog"
  }

  # Enable Secret Manager CSI driver
  secret_manager_config {
    enabled = true
  }

  # Enable addons
  addons_config {
    gcs_fuse_csi_driver_config {
      enabled = true
    }
  }

  # Configure maintenance window for reliability
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  depends_on = [
    google_project_service.apis,
    google_compute_network.main,
    google_compute_subnetwork.app_subnet
  ]
}

# Note: Autopilot clusters don't need node service accounts as Google manages them

# Service account for application workloads
resource "google_service_account" "app_workload" {
  account_id   = "dream-journal-app"
  project      = local.project_id
  display_name = "Dream Journal Application Service Account"
}

# IAM binding for Secret Manager access
resource "google_secret_manager_secret_iam_binding" "db_username_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.db_username.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "db_password_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "db_url_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.db_url.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "django_secret_key_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.django_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "django_admin_password_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.django_admin_password.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

resource "google_secret_manager_secret_iam_binding" "sendgrid_api_key_access" {
  project   = local.project_id
  secret_id = google_secret_manager_secret.sendgrid_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"

  members = [
    "serviceAccount:${google_service_account.app_workload.email}",
  ]
}

# Workload Identity binding
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.app_workload.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${local.project_id}.svc.id.goog[dream-journal/dream-journal-app]",
  ]

  depends_on = [google_container_cluster.dream_journal]
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

# Grant Cloud Build access to GKE
resource "google_project_iam_member" "cloudbuild_gke_admin" {
  project = local.project_id
  role    = "roles/container.admin"
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

# Global static IP for the load balancer
resource "google_compute_global_address" "dream_journal_ip" {
  name         = "dream-journal-ip"
  project      = local.project_id
  address_type = "EXTERNAL"

  depends_on = [google_project_service.apis]
}

# Cloud DNS managed zone (assuming it exists from Cloud Domains setup)
data "google_dns_managed_zone" "sensorium_dev" {
  name    = "sensorium-dev"
  project = local.project_id
}

# DNS A record pointing to the load balancer IP
resource "google_dns_record_set" "sensorium_dev_a" {
  name         = data.google_dns_managed_zone.sensorium_dev.dns_name
  managed_zone = data.google_dns_managed_zone.sensorium_dev.name
  type         = "A"
  ttl          = 300
  project      = local.project_id

  rrdatas = [google_compute_global_address.dream_journal_ip.address]
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
    resource.type="k8s_container"
    resource.labels.namespace_name="dream-journal"
    resource.labels.container_name="backend"
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
      filter          = "resource.type=\"k8s_container\" AND metric.type=\"logging.googleapis.com/user/${google_logging_metric.new_user_registrations.name}\""
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
