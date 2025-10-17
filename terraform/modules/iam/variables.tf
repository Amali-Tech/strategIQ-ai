# Iam Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Lambda permissions"
  type        = string
}

variable "campaign_tracking_policy_arn" {
  description = "ARN of the campaign tracking policy"
  type        = string
  default     = ""
}
