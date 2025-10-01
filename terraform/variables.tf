# Root Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "sandbox-034"
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

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID for cultural intelligence"
  type        = string
  default     = "KBRI4XYAXE"  # Empty string means no knowledge base
}