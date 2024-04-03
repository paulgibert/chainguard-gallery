output "url" {
  value = google_cloud_run_service.scanner.status[0].url
}