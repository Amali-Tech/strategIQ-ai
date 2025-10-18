resource "aws_lambda_function" "sentiment_analysis" {
  filename         = data.archive_file.sentiment_analysis_zip.output_path
  function_name    = "${var.project_name}-sentiment-analysis"
  role            = aws_iam_role.sentiment_analysis_lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.sentiment_analysis_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for comprehensive analysis
  memory_size     = 1024

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      BEDROCK_MODEL_ID    = "anthropic.claude-3-haiku-20240307-v1:0" 
      LOG_LEVEL          = "INFO"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.sentiment_analysis_lambda_policy]

  tags = var.tags
}

# Package the Lambda function
data "archive_file" "sentiment_analysis_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda/sentiment_analysis"
  output_path = "${path.module}/../../../lambda/sentiment_analysis.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache", "tests"]
}

# IAM Role for Lambda
resource "aws_iam_role" "sentiment_analysis_lambda_role" {
  name = "${var.project_name}-sentiment-analysis-lambda-role"

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

# Lambda Execution Policy
resource "aws_iam_role_policy_attachment" "sentiment_analysis_lambda_basic" {
  role       = aws_iam_role.sentiment_analysis_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom IAM Policy for Sentiment Analysis Lambda
resource "aws_iam_policy" "sentiment_analysis_lambda_policy" {
  name        = "${var.project_name}-sentiment-analysis-lambda-policy"
  description = "IAM policy for sentiment analysis Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream", 
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectSentiment",
          "comprehend:DetectEntities",
          "comprehend:DetectKeyPhrases",
          "comprehend:BatchDetectSentiment"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        ]
      },
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
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "sentiment_analysis_lambda_policy" {
  role       = aws_iam_role.sentiment_analysis_lambda_role.name
  policy_arn = aws_iam_policy.sentiment_analysis_lambda_policy.arn
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "sentiment_analysis_api_gateway" {
  count = var.enable_api_gateway ? 1 : 0

  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sentiment_analysis.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# Lambda Permission for Bedrock Agent
resource "aws_lambda_permission" "sentiment_analysis_bedrock_agent" {
  count = var.enable_bedrock_agent ? 1 : 0

  statement_id  = "AllowExecutionFromBedrockAgent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sentiment_analysis.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = var.bedrock_agent_arn
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "sentiment_analysis_logs" {
  name              = "/aws/lambda/${aws_lambda_function.sentiment_analysis.function_name}"
  retention_in_days = 14

  tags = var.tags
}

# Outputs
output "sentiment_analysis_lambda_arn" {
  description = "ARN of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.arn
}

output "sentiment_analysis_lambda_name" {
  description = "Name of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.function_name
}

output "sentiment_analysis_lambda_invoke_arn" {
  description = "Invoke ARN of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.invoke_arn
}