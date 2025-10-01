# Lambda Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

# IAM Role ARNs from IAM module
variable "lambda_image_analysis_role_arn" {
  description = "ARN of the Lambda image analysis execution role"
  type        = string
}

variable "lambda_campaign_role_arn" {
  description = "ARN of the Lambda campaign execution role"
  type        = string
}

variable "lambda_api_role_arn" {
  description = "ARN of the Lambda API execution role"
  type        = string
}

variable "lambda_sentiment_role_arn" {
  description = "ARN of the Lambda sentiment analysis execution role"
  type        = string
}

# Resource names from other modules
variable "s3_bucket_name" {
  description = "Name of the S3 bucket for images"
  type        = string
}

variable "product_analysis_table_name" {
  description = "Name of the product analysis DynamoDB table"
  type        = string
}

variable "enriched_data_table_name" {
  description = "Name of the enriched data DynamoDB table"
  type        = string
}

variable "comments_table_name" {
  description = "Name of the comments DynamoDB table for sentiment analysis"
  type        = string
}

variable "campaign_sqs_queue_url" {
  description = "URL of the SQS queue for campaign generation"
  type        = string
  default     = ""
}



# API Keys and Configuration
variable "youtube_api_key" {
  description = "YouTube Data API key"
  type        = string
  sensitive   = true
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for campaign generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
