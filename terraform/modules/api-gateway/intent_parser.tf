# Intent Parser Lambda Function
data "archive_file" "intent_parser_zip" {
  type        = "zip"
  source_file = "${path.root}/../lambda/intent_parser/handler.py"
  output_path = "${path.module}/zips/intent-parser.zip"
}

# IAM Role for Intent Parser Lambda
resource "aws_iam_role" "intent_parser_role" {
  name = "intent-parser-lambda-role"

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

# Basic execution policy
resource "aws_iam_role_policy_attachment" "intent_parser_basic_execution" {
  role       = aws_iam_role.intent_parser_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock permissions for Intent Parser
resource "aws_iam_role_policy" "intent_parser_bedrock_policy" {
  name = "intent-parser-bedrock-policy"
  role = aws_iam_role.intent_parser_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock-agent-runtime:InvokeAgent"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*",
          "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent-alias/*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeAgent"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Intent Parser Lambda Function
resource "aws_lambda_function" "intent_parser" {
  filename         = data.archive_file.intent_parser_zip.output_path
  function_name    = "bedrock-intent-parser"
  role            = aws_iam_role.intent_parser_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  source_code_hash = data.archive_file.intent_parser_zip.output_base64sha256

  description = "Intent parser for Bedrock multi-agent system - routes API requests to supervisor agent"

  environment {
    variables = {
      SUPERVISOR_AGENT_ID       = var.supervisor_agent_id
      SUPERVISOR_AGENT_ALIAS_ID = var.supervisor_agent_alias_id
    }
  }

  tags = var.tags
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "bedrock_api" {
  name          = "bedrock-multi-agent-api"
  protocol_type = "HTTP"
  description   = "HTTP API for Bedrock multi-agent marketing system"

  cors_configuration {
    allow_credentials = false
    allow_headers     = ["content-type", "authorization"]
    allow_methods     = ["POST", "OPTIONS"]
    allow_origins     = ["*"]
    max_age          = 86400
  }

  tags = var.tags
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "bedrock_api_stage" {
  api_id      = aws_apigatewayv2_api.bedrock_api.id
  name        = var.api_stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  tags = var.tags
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "intent_parser_integration" {
  api_id           = aws_apigatewayv2_api.bedrock_api.id
  integration_type = "AWS_PROXY"
  
  connection_type    = "INTERNET"
  description        = "Intent parser Lambda integration"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.intent_parser.invoke_arn
  
  payload_format_version = "2.0"
}

# API Routes
resource "aws_apigatewayv2_route" "campaigns_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /campaigns"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "cultural_analysis_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /cultural-analysis"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "market_analysis_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /market-analysis"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "sentiment_analysis_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /sentiment-analysis"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "image_analysis_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /image-analysis"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "translate_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /translate"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

resource "aws_apigatewayv2_route" "comprehensive_campaign_route" {
  api_id    = aws_apigatewayv2_api.bedrock_api.id
  route_key = "POST /comprehensive-campaign"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser_integration.id}"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.intent_parser.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bedrock_api.execution_arn}/*/*"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}