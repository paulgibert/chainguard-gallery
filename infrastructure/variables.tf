variable "project" {
    description = "The Google Cloud project ID"
    type = string
}

variable "region" {
    description = "The Google Cloud project region"
    type = string
}

variable "service_account" {
  description = "The name of the service account used for authentication"
  type = string
}

variable "image_repository" {
    description = "The Google Cloud image repository"
    type = string
}

variable "queue_name" {
  description = "The name of the Cloud Tasks queue that holds pending scans"
  type = string
}

variable "publisher_env_vars" {
    description = "A map of environment variables for the publisher service"
    type = map(string)
    default = {}
}

variable "scanner_env_vars" {
    description = "A map of environment variables for the scanner service"
    type = map(string)
    default = {}
}