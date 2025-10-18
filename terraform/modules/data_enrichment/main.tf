# Data Enrichment Module
# This module manages the data enrichment infrastructure for YouTube API integration

# Create ZIP file for Lambda function
data "archive_file" "data_enrichment_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/data_enrichment"
  output_path = "${path.module}/data_enrichment.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]
}

# Data enrichment Lambda function
resource "aws_lambda_function" "data_enrichment" {
  filename         = data.archive_file.data_enrichment_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-data-enrichment"
  role            = aws_iam_role.data_enrichment_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60  # YouTube API calls can take time
  memory_size     = 256

  source_code_hash = data.archive_file.data_enrichment_zip.output_base64sha256

  environment {
    variables = {
      YOUTUBE_API_KEY        = var.youtube_api_key
      DYNAMODB_TABLE_NAME    = aws_dynamodb_table.data_enrichment.name
    }
  }

  tags = {
    Environment = var.environment
    Name        = "${var.project_name}-${var.environment}-data-enrichment"
    Project     = var.project_name
    Purpose     = "Enrich marketing campaigns with YouTube data and trend analysis"
  }

  depends_on = [
    aws_iam_role_policy_attachment.data_enrichment_basic_execution,
    aws_iam_role_policy_attachment.data_enrichment_dynamodb_policy,
    aws_cloudwatch_log_group.data_enrichment_logs
  ]
}

# CloudWatch Log Group for Lambda function
resource "aws_cloudwatch_log_group" "data_enrichment_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-data-enrichment"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Data enrichment Lambda logs"
  }
}

# DynamoDB table for storing enrichment data
resource "aws_dynamodb_table" "data_enrichment" {
  name           = "${var.project_name}-${var.environment}-data-enrichment"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "enrichment_id"

  attribute {
    name = "enrichment_id"
    type = "S"
  }

  attribute {
    name = "search_query"
    type = "S"
  }

  # Global Secondary Index for querying by search query
  global_secondary_index {
    name               = "SearchQueryIndex"
    hash_key           = "search_query"
    projection_type    = "ALL"
  }

  # TTL configuration for automatic cleanup
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Environment = var.environment
    Name        = "${var.project_name}-${var.environment}-data-enrichment"
    Project     = var.project_name
    Purpose     = "Store YouTube enrichment data and insights"
  }
}

# IAM role for data enrichment Lambda function
resource "aws_iam_role" "data_enrichment_role" {
  name = "${var.project_name}-${var.environment}-data-enrichment-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Data enrichment Lambda execution role"
  }
}

# IAM policy for DynamoDB access
resource "aws_iam_policy" "data_enrichment_dynamodb_policy" {
  name        = "${var.project_name}-${var.environment}-data-enrichment-dynamodb-policy"
  description = "IAM policy for data enrichment Lambda to access DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.data_enrichment.arn,
          "${aws_dynamodb_table.data_enrichment.arn}/index/*"
        ]
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Data enrichment DynamoDB access policy"
  }
}

# Attach basic execution policy to the role
resource "aws_iam_role_policy_attachment" "data_enrichment_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.data_enrichment_role.name
}

# Attach DynamoDB policy to the role
resource "aws_iam_role_policy_attachment" "data_enrichment_dynamodb_policy" {
  policy_arn = aws_iam_policy.data_enrichment_dynamodb_policy.arn
  role       = aws_iam_role.data_enrichment_role.name
}

# Lambda permission for Bedrock to invoke the function
resource "aws_lambda_permission" "bedrock_invoke_data_enrichment" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_enrichment.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
}

# Data sources for current AWS region and account
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}