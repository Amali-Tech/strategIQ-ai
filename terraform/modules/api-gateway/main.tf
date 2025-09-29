# HTTP API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "HTTP API Gateway for ${var.project_name} ${var.environment}"

  cors_configuration {
    allow_credentials = false
    allow_headers     = ["*"]
    allow_methods     = ["*"]
    allow_origins     = ["*"]
    expose_headers    = ["*"]
    max_age           = 86400
  }

  tags = var.tags
}

# CloudWatch Logs for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7
  tags              = var.tags
}

# Stage with logging
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId   = "$context.requestId"
      httpMethod  = "$context.httpMethod"
      path        = "$context.path"
      status      = "$context.status"
      ip          = "$context.identity.sourceIp"
      responseTime= "$context.responseLatency"
    })
  }

  tags = var.tags
}

# Integration for Lambda (generate presigned URL)
resource "aws_apigatewayv2_integration" "presigned_url" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.generate_presigned_url_lambda_invoke_arn
  payload_format_version = "2.0"
}

# Integration for Lambda (get status)
resource "aws_apigatewayv2_integration" "get_status_function" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.get_status_lambda_invoke_arn
  payload_format_version = "2.0"
}

# Route for POST /presigned-url
resource "aws_apigatewayv2_route" "presigned_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /presigned-url"
  target    = "integrations/${aws_apigatewayv2_integration.presigned_url.id}"
}

# Route for GET /presigned-url
resource "aws_apigatewayv2_route" "get_status_function" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /status/{imageHash}"
  target    = "integrations/${aws_apigatewayv2_integration.get_status_function.id}"
}

resource "aws_apigatewayv2_route" "get_campaign_function" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /campaign/{imageHash}"
  target    = "integrations/${aws_apigatewayv2_integration.get_status_function.id}"
}