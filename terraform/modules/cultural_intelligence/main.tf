# Cultural Intelligence Lambda Module
# This module creates Lambda function for cultural adaptation and market intelligence

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Create ZIP file for Cultural Intelligence Lambda function
data "archive_file" "cultural_intelligence_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda/cultural_intelligence"
  output_path = "${path.module}/cultural_intelligence.zip"
}

# CloudWatch Log Group for Cultural Intelligence Lambda
resource "aws_cloudwatch_log_group" "cultural_intelligence_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-cultural-intelligence"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Cultural Intelligence Lambda
resource "aws_iam_role" "cultural_intelligence_role" {
  name = "${var.project_name}-${var.environment}-cultural-intelligence-role"

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
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Basic Lambda Execution
resource "aws_iam_role_policy_attachment" "cultural_intelligence_basic_execution" {
  role       = aws_iam_role.cultural_intelligence_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for DynamoDB Access
resource "aws_iam_policy" "cultural_intelligence_dynamodb_policy" {
  name        = "${var.project_name}-${var.environment}-cultural-intelligence-dynamodb-policy"
  description = "Policy for Cultural Intelligence Lambda to access DynamoDB"

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
          aws_dynamodb_table.cultural_intelligence.arn,
          "${aws_dynamodb_table.cultural_intelligence.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence-dynamodb-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Bedrock Knowledge Base Access (conditional)
resource "aws_iam_policy" "cultural_intelligence_bedrock_policy" {
  count       = var.cultural_intelligence_kb_arn != "" && var.market_intelligence_kb_arn != "" ? 1 : 0
  name        = "${var.project_name}-${var.environment}-cultural-intelligence-bedrock-policy"
  description = "Policy for Cultural Intelligence Lambda to access Bedrock Knowledge Bases"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = [
          var.cultural_intelligence_kb_arn,
          var.market_intelligence_kb_arn
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence-bedrock-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for S3 Knowledge Base Access
resource "aws_iam_policy" "cultural_intelligence_s3_policy" {
  name        = "${var.project_name}-${var.environment}-cultural-intelligence-s3-policy"
  description = "Policy for Cultural Intelligence Lambda to access S3 knowledge base documents"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_knowledge_base_bucket_name}",
          "arn:aws:s3:::${var.s3_knowledge_base_bucket_name}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence-s3-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach DynamoDB Policy to Role
resource "aws_iam_role_policy_attachment" "cultural_intelligence_dynamodb_policy" {
  role       = aws_iam_role.cultural_intelligence_role.name
  policy_arn = aws_iam_policy.cultural_intelligence_dynamodb_policy.arn
}

# Attach Bedrock Policy to Lambda Role (conditional)
resource "aws_iam_role_policy_attachment" "cultural_intelligence_bedrock_policy" {
  count      = var.cultural_intelligence_kb_arn != "" && var.market_intelligence_kb_arn != "" ? 1 : 0
  role       = aws_iam_role.cultural_intelligence_role.name
  policy_arn = aws_iam_policy.cultural_intelligence_bedrock_policy[0].arn
}

# Attach S3 Policy to Lambda Role
resource "aws_iam_role_policy_attachment" "cultural_intelligence_s3_policy" {
  role       = aws_iam_role.cultural_intelligence_role.name
  policy_arn = aws_iam_policy.cultural_intelligence_s3_policy.arn
}

# DynamoDB Table for Cultural Intelligence Data
resource "aws_dynamodb_table" "cultural_intelligence" {
  name           = "${var.project_name}-${var.environment}-cultural-intelligence"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "intelligence_id"

  attribute {
    name = "intelligence_id"
    type = "S"
  }

  attribute {
    name = "target_market"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying by target market
  global_secondary_index {
    name               = "TargetMarketIndex"
    hash_key           = "target_market"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Store cultural intelligence and market adaptation data"
  }
}

# Cultural Intelligence Lambda Function
resource "aws_lambda_function" "cultural_intelligence" {
  filename         = data.archive_file.cultural_intelligence_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-cultural-intelligence"
  role            = aws_iam_role.cultural_intelligence_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 120
  memory_size     = 512

  source_code_hash = data.archive_file.cultural_intelligence_zip.output_base64sha256

  environment {
    variables = {
      CULTURAL_INTELLIGENCE_KB_ID = var.cultural_intelligence_kb_id
      CULTURAL_KB_ID = var.cultural_intelligence_kb_id  # Backward compatibility
      MARKET_KB_ID = var.cultural_intelligence_kb_id    # Use same KB for both
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.cultural_intelligence.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.cultural_intelligence_basic_execution,
    aws_iam_role_policy_attachment.cultural_intelligence_dynamodb_policy,
    aws_iam_role_policy_attachment.cultural_intelligence_bedrock_policy,
    aws_cloudwatch_log_group.cultural_intelligence_logs
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Cultural adaptation and market intelligence"
  }
}

# Lambda Permission for Bedrock Agent to invoke the function
resource "aws_lambda_permission" "bedrock_invoke_cultural_intelligence" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cultural_intelligence.function_name
  principal     = "bedrock.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
}