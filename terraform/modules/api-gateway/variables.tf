# Api-gateway Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for image storage"
  type        = string
}

variable "cors_allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "upload_handler_invoke_arn" {
  description = "Invoke ARN of the upload handler Lambda function"
  type        = string
}

variable "upload_handler_function_name" {
  description = "Name of the upload handler Lambda function"
  type        = string
}

variable "intent_parser_invoke_arn" {
  description = "Invoke ARN of the intent parser Lambda function"
  type        = string
  default     = ""  # Optional until intent parser is deployed
}

variable "intent_parser_function_name" {
  description = "Name of the intent parser Lambda function"
  type        = string
  default     = ""  # Optional until intent parser is deployed
}
