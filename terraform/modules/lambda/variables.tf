# Lambda Module Variables

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

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "supervisor_agent_id" {
  description = "ID of the Bedrock supervisor agent"
  type        = string
  default     = ""  # Will be populated once Bedrock agent is created
}

variable "supervisor_agent_alias_id" {
  description = "Alias ID of the Bedrock supervisor agent"
  type        = string
  default     = ""  # Will be populated once Bedrock agent alias is created
}

variable "campaign_status_table_name" {
  description = "Name of the campaign status DynamoDB table"
  type        = string
  default     = ""
}

variable "campaign_events_bus_name" {
  description = "Name of the campaign events EventBridge bus"
  type        = string
  default     = ""
}

variable "visual_asset_queue_arn" {
  description = "ARN of the visual asset generation SQS queue"
  type        = string
  default     = ""
}

variable "image_analysis_role_arn" {
  description = "ARN of the dedicated IAM role for image analysis Lambda"
  type        = string
  default     = ""
}
