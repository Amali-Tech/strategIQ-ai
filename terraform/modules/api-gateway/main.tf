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

# Route: POST /api/upload/presigned-url
resource "aws_apigatewayv2_route" "presigned_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/upload/presigned-url"
  target    = "integrations/${aws_apigatewayv2_integration.presigned_url.id}"
}

# Route: GET /api/upload/{uploadId}
resource "aws_apigatewayv2_route" "upload_status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/upload/{uploadId}"
  target    = "integrations/${aws_apigatewayv2_integration.upload_status.id}"
}

# Integration for presigned URL generation
resource "aws_apigatewayv2_integration" "presigned_url" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.upload_handler_invoke_arn
  
  payload_format_version = "2.0"
}

# Integration for upload status checking (uses same Lambda function)
resource "aws_apigatewayv2_integration" "upload_status" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.upload_handler_invoke_arn
  
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

# Intent Parser Routes (only create if intent parser is deployed)
resource "aws_apigatewayv2_route" "campaigns" {
  count     = var.intent_parser_function_name != "" ? 1 : 0
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/campaigns"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser[0].id}"
}

resource "aws_apigatewayv2_route" "comprehensive_campaign" {
  count     = var.intent_parser_function_name != "" ? 1 : 0
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/comprehensive-campaign"
  target    = "integrations/${aws_apigatewayv2_integration.intent_parser[0].id}"
}

# Integration for intent parser
resource "aws_apigatewayv2_integration" "intent_parser" {
  count              = var.intent_parser_function_name != "" ? 1 : 0
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.intent_parser_invoke_arn
  
  payload_format_version = "2.0"
}

# Lambda permissions for API Gateway to invoke the intent parser function
resource "aws_lambda_permission" "api_gateway_invoke_intent_parser" {
  count         = var.intent_parser_function_name != "" ? 1 : 0
  statement_id  = "AllowExecutionFromAPIGateway-IntentParser"
  action        = "lambda:InvokeFunction"
  function_name = var.intent_parser_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}

# Route: GET /api/campaigns/{campaign_id}/status
resource "aws_apigatewayv2_route" "campaign_status_detail" {
  count     = var.campaign_status_function_name != "" ? 1 : 0
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/campaigns/{campaign_id}/status"
  target    = "integrations/${aws_apigatewayv2_integration.campaign_status[0].id}"
}

# Route: GET /api/campaigns/status (list campaigns)
resource "aws_apigatewayv2_route" "campaign_status_list" {
  count     = var.campaign_status_function_name != "" ? 1 : 0
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/campaigns/status"
  target    = "integrations/${aws_apigatewayv2_integration.campaign_status[0].id}"
}

# Integration for campaign status
resource "aws_apigatewayv2_integration" "campaign_status" {
  count              = var.campaign_status_function_name != "" ? 1 : 0
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.campaign_status_invoke_arn
  
  payload_format_version = "2.0"
}

# Lambda permissions for API Gateway to invoke the campaign status function
resource "aws_lambda_permission" "api_gateway_invoke_campaign_status" {
  count         = var.campaign_status_function_name != "" ? 1 : 0
  statement_id  = "AllowExecutionFromAPIGateway-CampaignStatus"
  action        = "lambda:InvokeFunction"
  function_name = var.campaign_status_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*/*"
}
