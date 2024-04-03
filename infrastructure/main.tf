terraform {
  required_providers {
    google = {
      version = "~> 5.21"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
}

module "publisher" {
  source  = "./modules/publisher"
  project = var.project
  location = var.region
  image_repository = var.image_repository
  env_vars = var.publisher_env_vars
  scanner_url = module.scanner.url
  service_account = var.service_account
}

module "scanner" {
  source  = "./modules/scanner"
  project = var.project
  location = var.region
  image_repository = var.image_repository
  env_vars = var.scanner_env_vars
}

resource "google_cloud_scheduler_job" "scheduler" {
  name = "scheduler"
  schedule = "0 * * * *"
  http_target {
    uri = module.publisher.url
    http_method = "POST"
    oidc_token {
      service_account_email = "${var.service_account}@${var.project}.iam.gserviceaccount.com"
      audience = module.publisher.url
    }
  }
  time_zone = "UTC"
}

resource "google_cloud_tasks_queue" "scan_queue" {
  name = "to-scan"
  location = var.region
  rate_limits {
    max_dispatches_per_second = 10
    max_concurrent_dispatches = 5
  }
  retry_config {
    max_attempts = 16
    max_retry_duration = "300s"
    min_backoff = "1s"
    max_backoff = "60s"
    max_doublings = 5
  }
}

resource "google_cloud_tasks_queue" "parse_queue" {
  name = "to-parse"
  location = var.region
  rate_limits {
    max_dispatches_per_second = 10
    max_concurrent_dispatches = 5
  }
  retry_config {
    max_attempts = 16
    max_retry_duration = "300s"
    min_backoff = "1s"
    max_backoff = "60s"
    max_doublings = 5
  }
}