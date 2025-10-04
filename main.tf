# Minimal Terraform configuration to prevent Terraform Cloud errors
# This repository no longer uses Terraform for infrastructure management

terraform {
  required_version = ">= 1.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Empty configuration - does nothing
resource "null_resource" "placeholder" {
  # This resource does nothing but prevents Terraform Cloud from erroring
}
