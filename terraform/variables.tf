variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "eu-west-1"
  
  validation {
    condition = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "lokalize-agent"
  
  validation {
    condition = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "aws_profile" {
  description = "aws profile"
  type        = string
}

variable "youtube_api_key" {
  description = "youtube api key"
  type        = string
}

variable "bedrock_agent_inference_profile_arn" {
  description = "Bedrock model inference profile arn to use for agent"
  type        = string
}

variable "bedrock_model_id" {
  description = "value"
  type        = string
}

variable "s3_allowed_origins" {
  description = "List of allowed origins for S3 CORS configuration"
  type        = list(string)
  default     = ["*"]
}

variable "supervisor_agent_alias_id_override" {
  description = "Override for supervisor agent alias ID (leave empty to use terraform-managed alias)"
  type        = string
  default     = ""
}

variable "cultural_intelligence_kb_id" {
  description = "Knowledge Base ID for cultural intelligence"
  type        = string
  default     = ""
}