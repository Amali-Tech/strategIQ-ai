# Lambda Module
# This module manages lambda resources for the AWS AI Hackathon project
# Deploys action group handlers + utility functions (not associated with Bedrock agent)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Create ZIP file for Lambda function
data "archive_file" "upload_handler_zip" {
  type        = "zip"
  source_file = "${path.root}/../lambda/upload-handler/handler.py"
  output_path = "${path.module}/upload_handler.zip"
}

# Upload handler Lambda function - Generates presigned S3 URLs
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
    Purpose     = "Generate presigned S3 URLs and check upload status"
  }
}

# Create ZIP file for Intent Parser Lambda function
data "archive_file" "intent_parser_zip" {
  type        = "zip"
  source_file = "${path.root}/../lambda/intent_parser/handler.py"
  output_path = "${path.module}/intent_parser.zip"
}

# Intent Parser Lambda function - Orchestrates Bedrock agent workflows
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

# Create ZIP file for Campaign Status Lambda function
data "archive_file" "campaign_status_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/campaign_status"
  output_path = "${path.module}/campaign_status.zip"
}

# Campaign Status Lambda function - Provides campaign status API endpoints
resource "aws_lambda_function" "campaign_status" {
  filename         = data.archive_file.campaign_status_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-campaign-status"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

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

# ============================================================================
# ACTION GROUP LAMBDA FUNCTIONS (not associated with Bedrock agent)
# ============================================================================

# Create ZIP file for Data Enrichment Lambda function
data "archive_file" "data_enrichment_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/data_enrichment"
  output_path = "${path.module}/data_enrichment.zip"
}

# Data Enrichment Lambda function - Enriches campaigns with YouTube data
resource "aws_lambda_function" "data_enrichment" {
  filename         = data.archive_file.data_enrichment_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-data-enrichment"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  source_code_hash = data.archive_file.data_enrichment_zip.output_base64sha256

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Data enrichment action group handler"
  }
}

# Create ZIP file for Image Analysis Lambda function
data "archive_file" "image_analysis_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/image_analysis"
  output_path = "${path.module}/image_analysis.zip"
}

# Image Analysis Lambda function - Analyzes product images using Rekognition
resource "aws_lambda_function" "image_analysis" {
  filename         = data.archive_file.image_analysis_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-image-analysis"
  role            = var.image_analysis_role_arn != "" ? var.image_analysis_role_arn : var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  source_code_hash = data.archive_file.image_analysis_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Image analysis action group handler"
  }
}

# Create ZIP file for Cultural Intelligence Lambda function
data "archive_file" "cultural_intelligence_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/cultural_intelligence"
  output_path = "${path.module}/cultural_intelligence.zip"
}

# Cultural Intelligence Lambda function - Provides cross-cultural insights
resource "aws_lambda_function" "cultural_intelligence" {
  filename         = data.archive_file.cultural_intelligence_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-cultural-intelligence"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  source_code_hash = data.archive_file.cultural_intelligence_zip.output_base64sha256

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Cultural intelligence action group handler"
  }
}

# Create ZIP file for Sentiment Analysis Lambda function
data "archive_file" "sentiment_analysis_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/sentiment_analysis"
  output_path = "${path.module}/sentiment_analysis.zip"
}

# Sentiment Analysis Lambda function - Analyzes market sentiment
resource "aws_lambda_function" "sentiment_analysis" {
  filename         = data.archive_file.sentiment_analysis_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-sentiment-analysis"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60

  source_code_hash = data.archive_file.sentiment_analysis_zip.output_base64sha256

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Sentiment analysis action group handler"
  }
}

# Create ZIP file for Visual Asset Generator Lambda function
data "archive_file" "visual_asset_generator_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/visual_asset_generator"
  output_path = "${path.module}/visual_asset_generator.zip"
}

# Visual Asset Generator Lambda function - Generates marketing assets
resource "aws_lambda_function" "visual_asset_generator" {
  filename         = data.archive_file.visual_asset_generator_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-visual-asset-generator"
  role            = var.lambda_execution_role_arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 120

  source_code_hash = data.archive_file.visual_asset_generator_zip.output_base64sha256

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Visual asset generator action group handler"
  }
}
