variable "project_root" {
  description = "Absolute path to the project root directory containing lambda-handlers"
  type        = string
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

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table used for campaign and image generation tracking"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for storing images"
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
  default     = "amazon.nova-canvas-v1:0"
}

variable "api_key_youtube" {
  description = "API key for YouTube Data API (if required by enrichment Lambda)"
  type        = string
  default     = ""
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
