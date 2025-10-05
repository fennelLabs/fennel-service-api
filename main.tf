# This repository no longer uses Terraform for infrastructure management
# Infrastructure is now managed via Kubernetes/Helm charts
# This file exists only to prevent Terraform Cloud errors

terraform {
  required_version = ">= 1.0"
  
  # If you have a Terraform Cloud backend configured, keep it here
  # Otherwise, comment out or remove the cloud block
  # cloud {
  #   organization = "fennellabs"
  #   workspaces {
  #     name = "fennel-service-api"
  #   }
  # }
  
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Empty placeholder resource - does nothing
resource "null_resource" "placeholder" {
  triggers = {
    note = "This repository no longer uses Terraform. Infrastructure is managed via Kubernetes."
  }
}

# Outputs to indicate the migration
output "migration_note" {
  value = "This repository has migrated from Terraform to Kubernetes/Helm chart deployment"
}
