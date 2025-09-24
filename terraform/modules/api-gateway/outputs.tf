# HTTP API Gateway Module Outputs

output "api_gateway_id" {
  description = "ID of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.main.id
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.main.execution_arn
}

output "api_gateway_invoke_url" {
  description = "Invoke URL of the HTTP API Gateway"
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "api_gateway_stage_name" {
  description = "Stage name of the HTTP API Gateway"
  value       = aws_apigatewayv2_stage.main.name
}

# Specific endpoint outputs
output "presigned_url_endpoint" {
  description = "Full URL for the presigned URL endpoint"
  value       = "${aws_apigatewayv2_stage.main.invoke_url}/presigned-url"
}

output "status_endpoint" {
  description = "Full URL for the status endpoint (without imageHash parameter)"
  value       = "${aws_apigatewayv2_stage.main.invoke_url}/status"
}

output "all_endpoints" {
  description = "Map of all available endpoints"
  value = {
    presigned_url = "${aws_apigatewayv2_stage.main.invoke_url}/presigned-url"
    status        = "${aws_apigatewayv2_stage.main.invoke_url}/status/{imageHash}"
  }
}