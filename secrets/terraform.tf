terraform {
  backend "s3" {
    bucket = "terraform.bostondsa.org"
    key    = "facebook-gcal-sync-secrets.tfstate"
    region = "us-east-1"
  }
}

locals {
  repo = "https://github.com/BostonDSA/facebook-gcal-sync.git"

  facebook_page_token     = var.facebook_page_token
  facebook_secret_name    = var.facebook_secret_name
  google_credentials_file = var.google_credentials_file
  google_secret_name      = var.google_secret_name
  release                 = var.release
}

provider "aws" {
  profile = "bdsa"
  region  = "us-east-1"
}

module "secrets" {
  # version                     = "~> 0.2"
  source = "github.com/amancevice/terraform-aws-facebook-gcal-sync-secrets"

  facebook_secret_description = "Access token for facebook.com/BostonDSA facebook page."
  google_secret_description   = "Google service account credentials for socialismbot."
  kms_key_alias               = "alias/aws/secretsmanager"

  facebook_page_token     = local.facebook_page_token
  facebook_secret_name    = local.facebook_secret_name
  google_secret_name      = local.google_secret_name
  google_credentials_file = local.google_credentials_file

  facebook_secret_tags = {
    App     = "facebook-gcal-sync"
    Release = local.release
    Repo    = local.repo
  }

  google_secret_tags = {
    App     = "facebook-gcal-sync"
    Release = local.release
    Repo    = local.repo
  }
}

output "facebook_secret_arn" {
  description = "facebook SecretsManager secret ARN"
  value       = module.secrets.facebook_secret.arn
}

output "facebook_secret_name" {
  description = "facebook SecretsManager secret name"
  value       = module.secrets.facebook_secret.name
}

output "google_secret_arn" {
  description = "Google service account SecretsManager secret ARN"
  value       = module.secrets.google_secret.arn
}

output "google_secret_name" {
  description = "Google service account SecretsManager secret name"
  value       = module.secrets.google_secret.name
}

variable "facebook_page_token" {
  description = "Page token for facebook.com/BostonDSA"
}

variable "facebook_secret_name" {
  description = "facebook SecretsManager secret name"
}

variable "google_credentials_file" {
  description = "Path to Google Service Account credentials file"
}

variable "google_secret_name" {
  description = "Google service account SecretsManager secret name"
}

variable "release" {
  description = "Release tag"
}
