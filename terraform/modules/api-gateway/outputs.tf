# API Gateway Module Outputs

output "api_gateway_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "api_gateway_invoke_url" {
  description = "Invoke URL of the API Gateway"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_gateway_stage_name" {
  description = "Stage name of the API Gateway deployment"  
  value       = aws_api_gateway_stage.main.stage_name
}

output "upload_endpoint" {
  description = "Full URL for the upload endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/upload"
}

output "status_endpoint" {
  description = "Full URL for the status endpoint (without imageHash parameter)"
  value       = "${aws_api_gateway_stage.main.invoke_url}/status"
}

# TODO: Add module outputs here
