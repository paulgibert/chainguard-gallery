resource "google_cloud_run_service" "publisher" {
  name = "publisher"
  location = var.location
  template {
    spec {
      containers {
        image = "${var.location}-docker.pkg.dev/${var.project}/${var.image_repository}/publisher:latest"
        resources {
          limits = {
            cpu = 1
            memory = "2Gi"
          }
        }
        ports {
          container_port = 8080
        }
        env {
          name = "SCANNER_URL"
          value = var.scanner_url
        }
        dynamic "env" {
          for_each = var.env_vars
          content {
            name = env.key
            value = env.value
          }
        }
      }
      service_account_name = "${var.service_account}@${var.project}.iam.gserviceaccount.com"
    }
  }
  traffic {
    percent = 100
      latest_revision = true
  }
  autogenerate_revision_name = true
}