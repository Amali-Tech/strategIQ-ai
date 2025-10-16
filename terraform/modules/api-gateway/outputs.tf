output "api_gateway_url" {
  description = "API Gateway HTTP API URL"
  value       = aws_apigatewayv2_api.bedrock_api.api_endpoint
}

output "api_gateway_stage_url" {
  description = "API Gateway stage URL"
  value       = "${aws_apigatewayv2_api.bedrock_api.api_endpoint}/${aws_apigatewayv2_stage.bedrock_api_stage.name}"
}

output "intent_parser_function_name" {
  description = "Intent parser Lambda function name"
  value       = aws_lambda_function.intent_parser.function_name
}

output "intent_parser_function_arn" {
  description = "Intent parser Lambda function ARN"
  value       = aws_lambda_function.intent_parser.arn
}

output "api_routes" {
  description = "Available API routes"
  value = {
    campaigns              = "POST /campaigns"
    cultural_analysis      = "POST /cultural-analysis"
    market_analysis        = "POST /market-analysis"
    sentiment_analysis     = "POST /sentiment-analysis"
    image_analysis         = "POST /image-analysis"
    translate              = "POST /translate"
    comprehensive_campaign = "POST /comprehensive-campaign"
  }
}
