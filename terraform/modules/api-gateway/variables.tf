# API Gateway Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "generate_presigned_url_lambda_invoke_arn" {
  description = "Invoke ARN of the generate presigned URL Lambda function"
  type        = string
}

variable "get_status_lambda_invoke_arn" {
  description = "Invoke ARN of the get status Lambda function"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# TODO: Add module-specific variables here
