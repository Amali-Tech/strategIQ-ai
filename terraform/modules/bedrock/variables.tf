# Bedrock Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for Bedrock model ARNs"
  type        = string
  default     = "eu-west-1"
}

variable "image_analysis_lambda_arn" {
  description = "ARN of the image analysis Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "data_enrichment_lambda_arn" {
  description = "ARN of the data enrichment Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "campaign_generation_lambda_arn" {
  description = "ARN of the campaign generation Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "voice_of_market_lambda_arn" {
  description = "ARN of the voice of market Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "lokalize_lambda_arn" {
  description = "ARN of the lokalize Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "cultural_intelligence_lambda_arn" {
  description = "ARN of the cultural intelligence Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "sentiment_analysis_lambda_arn" {
  description = "ARN of the sentiment analysis Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "visual_asset_generator_lambda_arn" {
  description = "ARN of the visual asset generator Lambda function"
  type        = string
  default     = ""  # Will be populated when Lambda is created
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use for the agent"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "bedrock_agent_inference_profile_arn" {
  description = "Bedrock agent inference profile ARN"
  type        = string
  default     = ""
}

variable "cultural_intelligence_kb_id" {
  description = "Knowledge Base ID for cultural intelligence"
  type        = string
  default     = ""
}