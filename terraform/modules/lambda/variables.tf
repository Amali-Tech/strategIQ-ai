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
  default     = "TSTALIASID"  # Default test alias
}
