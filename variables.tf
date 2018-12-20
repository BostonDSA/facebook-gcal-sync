variable app_name {
  description = "Name of app."
  default     = "facebook-gcal-sync"
}

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

variable event_rule_schedule_expression {
  description = "CloudWatch event rule expression"
  default     = "rate(1 hour)"
}

variable event_rule_is_enabled {
  description = "CloudWatch event rule enable/disable"
  default     = true
}

variable facebook_page_id {
  description = "facebook page ID."
}

variable facebook_secret_name {
  description = "facebook token SecretsManager secret name."
}

variable google_calendar_id {
  description = "Google Calendar ID."
}

variable google_secret_name {
  description = "Google service account SecretsManager secret name."
}

variable slack_author_icon {
  description = "Slack message author icon URL."
  default     = "https://en.facebookbrand.com/wp-content/themes/fb-branding/assets/favicons/apple-touch-icon-57x57.png"
}

variable slack_channel_alarms {
  description = "Slack channel where alarms are posted."
}

variable slack_channel_events {
  description = "Slack channel where events are posted."
}

variable slack_footer_icon {
  description = "Slack footer icon URL."
  default     = "https://assets-cdn.github.com/favicon.ico"
}

variable slack_footer_url {
  description = "Slack footer link URL."
  default     = "https://github.com/BostonDSA/facebook-gcal-sync"
}
