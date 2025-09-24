# HTTP API Gateway for AWS AI Hackathon

# Create the HTTP API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "HTTP API Gateway for ${var.project_name} ${var.environment}"

  # CORS configuration
  cors_configuration {
    allow_credentials = false
    allow_headers     = ["*"]
    allow_methods     = ["*"]
    allow_origins     = ["*"]
    expose_headers    = ["*"]
    max_age          = 86400
  }

  tags = var.tags
}

# Create the default stage with auto-deployment
resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  # Configure throttling
  default_route_settings {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }

  tags = var.tags
}

# Integration for generate presigned URL Lambda (POST /presigned-url)
resource "aws_apigatewayv2_integration" "presigned_url" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.generate_presigned_url_lambda_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Route for generate presigned URL endpoint
resource "aws_apigatewayv2_route" "presigned_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /presigned-url"
  target    = "integrations/${aws_apigatewayv2_integration.presigned_url.id}"
  
  authorization_type = "NONE"
}

# Integration for get status Lambda (GET /status/{imageHash})
resource "aws_apigatewayv2_integration" "status" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.get_status_lambda_invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Route for get status endpoint
resource "aws_apigatewayv2_route" "status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /status/{imageHash}"
  target    = "integrations/${aws_apigatewayv2_integration.status.id}"
  
  authorization_type = "NONE"
}