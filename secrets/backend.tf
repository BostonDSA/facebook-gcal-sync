terraform {
  backend s3 {
    bucket  = "terraform.bostondsa.org"
    key     = "facebook-gcal-sync-secrets.tfstate"
    region  = "us-east-1"
    profile = "bdsa"
  }
}
