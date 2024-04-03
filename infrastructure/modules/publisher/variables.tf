variable "project" {
    description = "The Google Cloud project ID"
    type = string
}

variable "location" {
    description = "The Google Cloud location to deploy the Cloud Run service"
    type = string
}

variable "image_repository" {
    description = "The Google Cloud image repository"
    type = string
}

variable "env_vars" {
    description = "A map of environment variables for the Cloud Run service"
    type = map(string)
    default = {}
}

variable "scanner_url" {
    description = "The URL of the Cloud Run scanner service"
    type = string
}

variable "service_account" {
  description = "The name of the service account used for authentication"
  type = string
}