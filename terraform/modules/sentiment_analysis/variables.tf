variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for storing analysis results"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for storing analysis results"
  type        = string
}

variable "enable_api_gateway" {
  description = "Whether to enable API Gateway integration"
  type        = bool
  default     = false
}

variable "api_gateway_execution_arn" {
  description = "ARN of the API Gateway execution role"
  type        = string
  default     = ""
}

variable "enable_bedrock_agent" {
  description = "Whether to enable Bedrock agent integration"
  type        = bool
  default     = false
}

variable "bedrock_agent_arn" {
  description = "ARN of the Bedrock agent"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}