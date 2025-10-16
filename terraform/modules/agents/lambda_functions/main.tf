# Lambda Functions Module for Bedrock Agent Action Groups

# Data sources for current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  lambda_functions = var.functions
}

# Create ZIP files for each Lambda function
data "archive_file" "lambda_zip" {
  for_each = local.lambda_functions
  
  type        = "zip"
  source_file = "${each.value.handler_path}/handler.py"
  output_path = "${path.module}/zips/${var.agent_name}-${each.key}.zip"
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_execution_role" {
  for_each = local.lambda_functions
  
  name = "${var.agent_name}-${each.key}-lambda-role"

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

  tags = var.tags
}

# Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  for_each = local.lambda_functions
  
  role       = aws_iam_role.lambda_execution_role[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Additional IAM policy for Bedrock and other AWS services
resource "aws_iam_role_policy" "lambda_bedrock_policy" {
  for_each = local.lambda_functions
  
  name = "${var.agent_name}-${each.key}-bedrock-policy"
  role = aws_iam_role.lambda_execution_role[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "s3:GetObject",
          "s3:PutObject",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Functions
resource "aws_lambda_function" "action_group_lambda" {
  for_each = local.lambda_functions
  
  filename         = data.archive_file.lambda_zip[each.key].output_path
  function_name    = "${var.agent_name}-${each.key}"
  role            = aws_iam_role.lambda_execution_role[each.key].arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256

  source_code_hash = data.archive_file.lambda_zip[each.key].output_base64sha256

  description = each.value.description

  environment {
    variables = {
      AGENT_NAME = var.agent_name
      FUNCTION_NAME = each.key
    }
  }

  tags = var.tags
}

# Lambda permissions for Bedrock Agent
resource "aws_lambda_permission" "allow_bedrock_agent" {
  for_each = local.lambda_functions
  
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.action_group_lambda[each.key].function_name
  principal     = "bedrock.amazonaws.com"
  
  # Allow Bedrock agents in current account and region to invoke this function
  source_arn = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
}