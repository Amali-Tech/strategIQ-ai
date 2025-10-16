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
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Parse intents and orchestrate Bedrock agent workflows"
  }
}
