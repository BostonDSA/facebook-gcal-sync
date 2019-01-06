provider aws {
  version    = "~> 1.54"
  access_key = "${var.aws_access_key_id}"
  secret_key = "${var.aws_secret_access_key}"
  profile    = "${var.aws_profile}"
  region     = "${var.aws_region}"
}

module secrets {
  source                      = "amancevice/facebook-gcal-sync-secrets/aws"
  version                     = "0.1.0"
  facebook_page_token         = "${var.facebook_page_token}"
  facebook_secret_description = "Access token for facebook.com/BostonDSA facebook page."
  facebook_secret_name        = "${var.facebook_secret_name}"
  google_secret_description   = "Google service account credentials for socialismbot."
  google_secret_name          = "${var.google_secret_name}"
  google_credentials_file     = "${var.google_credentials_file}"
  kms_key_alias               = "alias/aws/secretsmanager"

  facebook_secret_tags {
    App     = "facebook-gcal-sync"
    Release = "${var.release}"
    Repo    = "${var.repo}"
  }

  google_secret_tags {
    App     = "facebook-gcal-sync"
    Release = "${var.release}"
    Repo    = "${var.repo}"
  }
}
