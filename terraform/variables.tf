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

variable "project_root" {
  description = "Absolute path to the project root directory containing lambda-handlers"
  type        = string
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


variable "s3_allowed_origins" {
  description = "List of allowed origins for S3 CORS configuration"
  type        = list(string)
  default     = ["*"]
}

variable "products_table_name" {
  description = "Name of the DynamoDB table for products and analysis records"
  type        = string
  default     = "products"
}

variable "generated_images_table_name" {
  description = "Name of the DynamoDB table for generated image metadata and status"
  type        = string
  default     = "generated_images"
}

variable "image_generation_queue_name" {
  description = "Name of the SQS queue for image generation requests"
  type        = string
  default     = "image-generation-queue"
}

variable "lambda_image_analysis_function_name" {
  description = "Name of the image analysis Lambda function"
  type        = string
}

variable "lambda_data_enrichment_function_name" {
  description = "Name of the data enrichment Lambda function"
  type        = string
}

variable "lambda_cultural_intelligence_function_name" {
  description = "Name of the cultural intelligence Lambda function"
  type        = string
}

variable "lambda_intent_parser_function_name" {
  description = "Name of the intent parser Lambda function"
  type        = string
}

variable "lambda_generate_images_function_name" {
  description = "Name of the image generation Lambda function"
  type        = string
}

variable "lambda_image_generation_status_function_name" {
  description = "Name of the image generation status Lambda function"
  type        = string
}

variable "bedrock_agent_id" {
  description = "Bedrock agent ID for campaign orchestration"
  type        = string
}

variable "bedrock_agent_alias_id" {
  description = "Bedrock agent alias ID for campaign orchestration"
  type        = string
}

variable "bedrock_nova_canvas_model_id" {
  description = "Bedrock model ID for Nova Canvas image generation"
  type        = string
}

variable "api_key_other" {
  description = "Other external API keys required by Lambda functions (optional)"
  type        = string
  default     = ""
}

variable "lambda_upload_handler_function_name" {
  description = "Name of the upload handler Lambda function"
  type        = string
}

