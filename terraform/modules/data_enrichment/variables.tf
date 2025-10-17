# Data Enrichment Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "youtube_api_key" {
  description = "YouTube Data API v3 key for content enrichment"
  type        = string
  sensitive   = true
}