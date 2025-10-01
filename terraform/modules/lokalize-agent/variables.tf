# Lokalize Agent Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID for cultural intelligence"
  type        = string
  default     = "XMODLTJFEH"
}

variable "agent_name" {
  description = "Name of the Bedrock Agent"
  type        = string
  default     = "Lokalize-Marketing-Agent"
}

variable "schemas_bucket_name" {
  description = "S3 bucket name containing OpenAPI schemas"
  type        = string
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role for Lokalize functions"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}