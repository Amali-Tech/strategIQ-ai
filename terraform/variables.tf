# Root Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "aws-ai-hackathon"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "youtube_api_key" {
  description = "YouTube Data API key for video enrichment"
  type        = string
  sensitive   = true
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for campaign generation"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}