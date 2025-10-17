# Lambda Module
# This module manages lambda resources for the AWS AI Hackathon project

# Create ZIP file for Lambda function
data "archive_file" "upload_handler_zip" {
  type        = "zip"
  source_file = "${path.root}/../lambda/upload-handler/handler.py"
  output_path = "${path.module}/upload_handler.zip"
}

# Upload handler Lambda function
resource "aws_lambda_function" "upload_handler" {
  filename         = data.archive_file.upload_handler_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-upload-handler"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  source_code_hash = data.archive_file.upload_handler_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name
      PRESIGNED_URL_EXPIRATION = "3600"
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Handle image upload presigned URLs and status checking"
  }
}

# Create ZIP file for Intent Parser Lambda function
data "archive_file" "intent_parser_zip" {
  type        = "zip"
  source_file = "${path.root}/../lambda/intent_parser/handler.py"
  output_path = "${path.module}/intent_parser.zip"
}

# Intent Parser Lambda function
resource "aws_lambda_function" "intent_parser" {
  filename         = data.archive_file.intent_parser_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-intent-parser"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for complex orchestration

  source_code_hash = data.archive_file.intent_parser_zip.output_base64sha256

  environment {
    variables = {
      SUPERVISOR_AGENT_ID = var.supervisor_agent_id
      SUPERVISOR_AGENT_ALIAS_ID = var.supervisor_agent_alias_id
      CAMPAIGN_STATUS_TABLE_NAME = var.campaign_status_table_name
      CAMPAIGN_EVENTS_BUS_NAME = var.campaign_events_bus_name
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Parse intents and orchestrate Bedrock agent workflows"
  }
}

# Create ZIP file for Async Visual Processor Lambda function
data "archive_file" "async_visual_processor_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/async_visual_processor"
  output_path = "${path.module}/async_visual_processor.zip"
}

# Async Visual Processor Lambda function
resource "aws_lambda_function" "async_visual_processor" {
  filename         = data.archive_file.async_visual_processor_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-async-visual-processor"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 900  # 15 minutes for visual asset generation

  source_code_hash = data.archive_file.async_visual_processor_zip.output_base64sha256

  environment {
    variables = {
      CAMPAIGN_STATUS_TABLE_NAME = var.campaign_status_table_name
      VISUAL_ASSET_GENERATOR_FUNCTION_NAME = "${var.project_name}-${var.environment}-visual-asset-generator"
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Process async visual asset generation from SQS events"
  }
}

# SQS Event Source Mapping for async visual processor
resource "aws_lambda_event_source_mapping" "async_visual_processor_sqs" {
  count            = var.visual_asset_queue_arn != "" ? 1 : 0
  event_source_arn = var.visual_asset_queue_arn
  function_name    = aws_lambda_function.async_visual_processor.arn
  batch_size       = 1  # Process one campaign at a time
  
  # Enable partial batch failure reporting
  function_response_types = ["ReportBatchItemFailures"]
}

# Create ZIP file for Campaign Status Lambda function
data "archive_file" "campaign_status_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/campaign_status"
  output_path = "${path.module}/campaign_status.zip"
}

# Campaign Status Lambda function
resource "aws_lambda_function" "campaign_status" {
  filename         = data.archive_file.campaign_status_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-campaign-status"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30  # Short timeout for status queries

  source_code_hash = data.archive_file.campaign_status_zip.output_base64sha256

  environment {
    variables = {
      CAMPAIGN_STATUS_TABLE_NAME = var.campaign_status_table_name
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Provide campaign status API endpoints"
  }
}
