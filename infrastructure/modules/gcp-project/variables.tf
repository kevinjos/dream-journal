# Variables for GCP Project Module

variable "project_id" {
  description = "Existing GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
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

# Note: GKE Autopilot doesn't use node configuration variables
# Resources are automatically managed based on pod resource requests

# Database Variables
variable "db_tier" {
  description = "Cloud SQL database tier"
  type        = string
  default     = "db-f1-micro"
}

# GitHub Repository Variables for Cloud Build Triggers
variable "github_owner" {
  description = "GitHub repository owner/organization"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}