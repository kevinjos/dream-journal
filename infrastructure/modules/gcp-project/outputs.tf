# Outputs for GCP Project Module

output "project_id" {
  description = "The GCP project ID"
  value       = data.google_project.sensorium.project_id
}

output "project_number" {
  description = "The GCP project number"
  value       = data.google_project.sensorium.number
}

output "project_name" {
  description = "The GCP project name"
  value       = data.google_project.sensorium.name
}

output "vpc_network_id" {
  description = "The VPC network ID"
  value       = google_compute_network.main.id
}

output "vpc_network_name" {
  description = "The VPC network name"
  value       = google_compute_network.main.name
}

output "app_subnet_id" {
  description = "The application subnet ID"
  value       = google_compute_subnetwork.app_subnet.id
}

output "app_subnet_name" {
  description = "The application subnet name"
  value       = google_compute_subnetwork.app_subnet.name
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

output "zone" {
  description = "The GCP zone"
  value       = var.zone
}

# GKE Outputs
output "gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.dream_journal.name
}

output "gke_cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = google_container_cluster.dream_journal.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "Base64 encoded CA certificate for the GKE cluster"
  value       = google_container_cluster.dream_journal.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

# Database Outputs
output "db_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.name
}

output "db_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

# Secret Manager Outputs
output "db_username_secret_name" {
  description = "Name of the Secret Manager secret containing database username"
  value       = google_secret_manager_secret.db_username.secret_id
}

output "db_password_secret_name" {
  description = "Name of the Secret Manager secret containing database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "db_url_secret_name" {
  description = "Name of the Secret Manager secret containing database URL"
  value       = google_secret_manager_secret.db_url.secret_id
}

output "django_secret_key_secret_name" {
  description = "Name of the Secret Manager secret containing Django secret key"
  value       = google_secret_manager_secret.django_secret_key.secret_id
}

output "django_admin_password_secret_name" {
  description = "Name of the Secret Manager secret containing Django admin password"
  value       = google_secret_manager_secret.django_admin_password.secret_id
}

output "django_admin_password" {
  description = "Django admin password (sensitive - use 'terraform output -raw django_admin_password' to view)"
  value       = random_password.django_admin_password.result
  sensitive   = true
}

# Service Account Outputs
output "app_service_account_email" {
  description = "Email of the application service account for Workload Identity"
  value       = google_service_account.app_workload.email
}

# Artifact Registry Outputs
output "docker_repository" {
  description = "Docker repository URL"
  value       = "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

# Networking Outputs
output "static_ip_address" {
  description = "Static IP address for the load balancer"
  value       = google_compute_global_address.dream_journal_ip.address
}

output "dns_name_servers" {
  description = "DNS name servers for the domain"
  value       = data.google_dns_managed_zone.sensorium_dev.name_servers
}
