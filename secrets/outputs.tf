output facebook_secret_arn {
  description = "facebook SecretsManager secret ARN."
  value       = "${module.secrets.facebook_secret_arn}"
}

output facebook_secret_name {
  description = "facebook SecretsManager secret name."
  value       = "${module.secrets.facebook_secret_name}"
}

output google_secret_arn {
  description = "Google service account SecretsManager secret ARN."
  value       = "${module.secrets.google_secret_arn}"
}

output google_secret_name {
  description = "Google service account SecretsManager secret name."
  value       = "${module.secrets.google_secret_name}"
}
