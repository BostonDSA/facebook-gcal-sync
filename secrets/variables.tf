variable aws_access_key_id {
  description = "AWS Access Key ID."
  default     = ""
}

variable aws_secret_access_key {
  description = "AWS Secret Access Key."
  default     = ""
}

variable aws_profile {
  description = "AWS Profile."
  default     = ""
}

variable aws_region {
  description = "AWS Region."
  default     = "us-east-1"
}

variable facebook_page_token {
  description = "Page token for facebook.com/BostonDSA."
}

variable facebook_secret_name {
  description = "facebook SecretsManager secret name."
}

variable google_credentials_file {
  description = "Path to Google Service Account credentials file."
}

variable google_secret_name {
  description = "Google service account SecretsManager secret name."
}
