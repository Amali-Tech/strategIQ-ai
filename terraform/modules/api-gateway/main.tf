# Api-gateway Module
# This module manages api-gateway resources for the AWS AI Hackathon project

# HTTP API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "HTTP API for Lokalize Agent image upload and processing"

  cors_configuration {
    allow_credentials = false
    allow_headers     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins     = var.cors_allowed_origins
    expose_headers    = ["*"]
    max_age          = 86400
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Image upload and campaign processing API"
  }
}

# --- Campaign Generation Endpoint ---
resource "aws_apigatewayv2_route" "campaign_tier_1" {
  count     = var.intent_parser_function_name != "" ? 1 : 0
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/campaigns/tier-1"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser[0].id}"
}

# --- Upload Endpoints ---
resource "aws_apigatewayv2_route" "presigned_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/uploads/presigned-url"
  target    = "integrations/${aws_apigatewayv2_integration.presigned_url.id}"
}

resource "aws_apigatewayv2_route" "upload_status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/uploads/{uploadId}"
  target    = "integrations/${aws_apigatewayv2_integration.upload_status.id}"
}

resource "aws_apigatewayv2_integration" "presigned_url" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.upload_handler_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "upload_status" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.upload_handler_invoke_arn
  payload_format_version = "2.0"
}

# --- Asset Generation Endpoints ---
resource "aws_apigatewayv2_route" "assets_post" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/assets/"
  target    = "integrations/${aws_apigatewayv2_integration.assets_sqs.id}"
}

resource "aws_apigatewayv2_route" "assets_status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/assets/{request_id}"
  target    = "integrations/${aws_apigatewayv2_integration.assets_status.id}"
}

resource "aws_apigatewayv2_integration" "assets_sqs" {
  api_id                = aws_apigatewayv2_api.main.id
  integration_type      = "AWS_PROXY"
  integration_method    = "POST"
  integration_uri       = var.assets_sqs_arn
  integration_subtype   = "SQS-SendMessage"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "assets_status" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.image_generation_status_invoke_arn
  payload_format_version = "2.0"
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit   = 1000
    throttling_burst_limit  = 2000
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda permissions for API Gateway to invoke the upload handler function
resource "aws_lambda_permission" "api_gateway_invoke_presigned_url" {
  statement_id  = "AllowExecutionFromAPIGateway-PresignedURL"
  action        = "lambda:InvokeFunction"
  function_name = var.upload_handler_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_invoke_upload_status" {
  statement_id  = "AllowExecutionFromAPIGateway-UploadStatus"
  action        = "lambda:InvokeFunction"
  function_name = var.upload_handler_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}

# Lambda permission for campaign generation (intent parser)
resource "aws_lambda_permission" "api_gateway_invoke_intent_parser" {
  count         = var.intent_parser_function_name != "" ? 1 : 0
  statement_id  = "AllowExecutionFromAPIGateway-IntentParser"
  action        = "lambda:InvokeFunction"
  function_name = var.intent_parser_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}

# Lambda permission for image generation status
resource "aws_lambda_permission" "api_gateway_invoke_image_generation_status" {
  statement_id  = "AllowExecutionFromAPIGateway-ImageGenerationStatus"
  action        = "lambda:InvokeFunction"
  function_name = var.image_generation_status_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}

resource "aws_apigatewayv2_integration" "intent_parser" {
  count                  = var.intent_parser_function_name != "" ? 1 : 0
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = var.intent_parser_invoke_arn
  payload_format_version = "2.0"
}
