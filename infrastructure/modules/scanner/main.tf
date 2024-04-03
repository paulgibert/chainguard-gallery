resource "google_cloud_run_service" "scanner" {
  name = "scanner"
  location = var.location
  template {
    spec {
      containers {
        image = "${var.location}-docker.pkg.dev/${var.project}/${var.image_repository}/parser:latest"
        resources {
          limits = {
            cpu = 4
            memory = "16Gi"
          }
        }
        ports {
          container_port = 8080
        }
        dynamic "env" {
          for_each = var.env_vars
          content {
            name = env.key
            value = env.value
          }
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "125"
        "autoscaling.knative.dev/concurrency" = "1"
      }
    }
  }
  traffic {
    percent = 100
      latest_revision = true
  }
  autogenerate_revision_name = true
}