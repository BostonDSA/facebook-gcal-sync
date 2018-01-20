variable "FACEBOOK_APP_ID" {
  description = "Facebook App ID (TF_VAR_facebook_app_id)"
}

variable "FACEBOOK_APP_SECRET" {
  description = "Facebook App secret (TF_VAR_facebook_app_secret)"
}

variable "HEROKU_APP_NAME" {
  description = "Name of the app on heroku"
}

variable "HEROKU_APP_REGION" {
  description = "Heroku region"
  default     = "us"
}

variable "HEROKU_API_KEY" {
  description = "Heroku API Key (TF_VAR_heroku_api_key)"
}

variable "HEROKU_STACK" {
  description = "Heroku stack"
  default     = "heroku-16"
}

variable "DEADMANSSNITCH_URL" {
  description = "Dead Man's Snitch URL (TF_VAR_deadmanssnitch_url)"
}

variable "GOOGLE_ACCOUNT_TYPE" {
  description = "Google Cloud acct type (TF_VAR_google_account_type)"
}

variable "GOOGLE_CALENDAR_ID" {
  description = "Google Calendar ID (TF_VAR_google_calendar_id)"
}

variable "GOOGLE_CLIENT_EMAIL" {
  description = "Google Client email (TF_VAR_google_client_email)"
}

variable "GOOGLE_CLIENT_ID" {
  description = "Google Client ID (TF_VAR_google_client_id)"
}

variable "GOOGLE_PRIVATE_KEY" {
  description = "Google Private Key (TF_VAR_google_private_key)"
}

variable "GOOGLE_PRIVATE_KEY_ID" {
  description = "Google Private Key ID (TF_VAR_google_private_key_id)"
}

variable "GOOGLE_SCOPE" {
  description = "Google Scope (TF_VAR_google_scope)"
}

variable "TRIBE_ENDPOINT" {
  description = "Tribe API endpoint (TF_VAR_tribe_endpoint)"
}

variable "WORDPRESS_APP_PASSWORD" {
  description = "WordPress App password (TF_VAR_wordpress_app_password)"
}

variable "WORDPRESS_ENDPOINT" {
  description = "WordPress endpoint (TF_VAR_wordpress_endpoint)"
}

variable "WORDPRESS_USERNAME" {
  description = "WordPress username (TF_VAR_wordpress_username)"
}

variable "WP_CUSTOM_FIELD_BODY" {
  description = "WordPress Post custom field 'body' (TF_VAR_wp_custom_field_body)"
}

variable "WP_CUSTOM_FIELD_HEADER" {
  description = "WordPress Post custom field 'header' (TF_VAR_wp_custom_field_header)"
}

variable "WP_CUSTOM_FIELD_LINK_TEXT" {
  description = "WordPress Post custom field 'link_text' (TF_VAR_wp_custom_field_link_text)"
}

variable "WP_CUSTOM_FIELD_LINK_URL" {
  description = "WordPress Post custom field 'link_url' (TF_VAR_wp_custom_field_link_url)"
}

provider "heroku" {
  api_key = "${var.HEROKU_API_KEY}"
  version = "~> 0.1"
}

resource "heroku_app" "boston_dsa_event_sync" {
  name       = "${var.HEROKU_APP_NAME}"
  region     = "${var.HEROKU_APP_REGION}"
  stack      = "${var.HEROKU_STACK}"
  buildpacks = ["heroku/python"]

  config_vars {
    DEADMANSSNITCH_URL        = "${var.DEADMANSSNITCH_URL}"
    FACEBOOK_APP_ID           = "${var.FACEBOOK_APP_ID}"
    FACEBOOK_APP_SECRET       = "${var.FACEBOOK_APP_SECRET}"
    GOOGLE_ACCOUNT_TYPE       = "${var.GOOGLE_ACCOUNT_TYPE}"
    GOOGLE_CALENDAR_ID        = "${var.GOOGLE_CALENDAR_ID}"
    GOOGLE_CLIENT_EMAIL       = "${var.GOOGLE_CLIENT_EMAIL}"
    GOOGLE_CLIENT_ID          = "${var.GOOGLE_CLIENT_ID}"
    GOOGLE_PRIVATE_KEY        = "${var.GOOGLE_PRIVATE_KEY}"
    GOOGLE_PRIVATE_KEY_ID     = "${var.GOOGLE_PRIVATE_KEY_ID}"
    GOOGLE_SCOPE              = "${var.GOOGLE_SCOPE}"
    TRIBE_ENDPOINT            = "${var.TRIBE_ENDPOINT}"
    WORDPRESS_APP_PASSWORD    = "${var.WORDPRESS_APP_PASSWORD}"
    WORDPRESS_ENDPOINT        = "${var.WORDPRESS_ENDPOINT}"
    WORDPRESS_USERNAME        = "${var.WORDPRESS_USERNAME}"
    WP_CUSTOM_FIELD_BODY      = "${var.WP_CUSTOM_FIELD_BODY}"
    WP_CUSTOM_FIELD_HEADER    = "${var.WP_CUSTOM_FIELD_HEADER}"
    WP_CUSTOM_FIELD_LINK_TEXT = "${var.WP_CUSTOM_FIELD_LINK_TEXT}"
    WP_CUSTOM_FIELD_LINK_URL  = "${var.WP_CUSTOM_FIELD_LINK_URL}"
  }
}
