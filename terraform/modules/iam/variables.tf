# Iam Module Variables

# TODO: Add module-specific variables here

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs"
  type        = list(string)
}

variable "dynamodb_stream_arns" {
  description = "List of DynamoDB stream ARNs"
  type        = list(string)
}

variable "sqs_queue_arns" {
  description = "List of SQS queue ARNs"
  type        = list(string)
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs"
  type        = list(string)
  default     = ["*"]  # Will be updated after Lambda functions are created
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
