# Production Environment for Dream Journal
terraform {
  required_version = ">= 1.6"

  backend "gcs" {
    bucket = "sensorium-terraform-state"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Configure the existing Sensorium project infrastructure
module "gcp_project" {
  source = "../../modules/gcp-project"

  project_id  = var.project_id
  environment = "prod"
  region      = var.region
  zone        = var.zone

  # Note: No GKE node configuration needed for Autopilot

  # Database Configuration
  db_tier = var.db_tier

  # GitHub Repository Configuration
  github_owner = var.github_owner
  github_repo  = var.github_repo

  # Monitoring Configuration
  alert_email = var.alert_email
}
