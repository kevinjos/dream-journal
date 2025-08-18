# Outputs for Production Environment

output "project_id" {
  description = "The GCP project ID"
  value       = module.gcp_project.project_id
}

output "project_number" {
  description = "The GCP project number"
  value       = module.gcp_project.project_number
}

output "vpc_network_name" {
  description = "The VPC network name"
  value       = module.gcp_project.vpc_network_name
}

output "app_subnet_name" {
  description = "The application subnet name"
  value       = module.gcp_project.app_subnet_name
}

output "region" {
  description = "The GCP region"
  value       = module.gcp_project.region
}