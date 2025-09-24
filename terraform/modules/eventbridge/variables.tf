# EventBridge Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "eventbridge_pipes_role_arn" {
  description = "ARN of the EventBridge Pipes execution role"
  type        = string
}

# DynamoDB Stream ARNs
variable "product_analysis_stream_arn" {
  description = "ARN of the product analysis DynamoDB stream"
  type        = string
}

variable "enriched_data_stream_arn" {
  description = "ARN of the enriched data DynamoDB stream"
  type        = string
}

variable "campaign_data_stream_arn" {
  description = "ARN of the campaign data DynamoDB stream"
  type        = string
}

# Lambda Function ARNs
variable "enrichment_lambda_arn" {
  description = "ARN of the enrichment Lambda function"
  type        = string
}

variable "campaign_generator_lambda_arn" {
  description = "ARN of the campaign generator Lambda function"
  type        = string
}

variable "campaign_generator_lambda_name" {
  description = "Name of the campaign generator Lambda function"
  type        = string
}

# SQS Queue ARN
variable "campaign_sqs_queue_arn" {
  description = "ARN of the campaign generation SQS queue"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# TODO: Add module-specific variables here
