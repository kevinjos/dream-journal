# Variables for Production Environment

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

# Note: GKE Autopilot doesn't require node configuration variables

# Database Variables
variable "db_tier" {
  description = "Cloud SQL database tier"
  type        = string
  default     = "db-f1-micro"
}

# GitHub Repository Variables
variable "github_owner" {
  description = "GitHub repository owner/organization"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}