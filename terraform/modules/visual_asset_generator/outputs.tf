output "lambda_function_name" {
  description = "Name of the Visual Asset Generator Lambda function"
  value       = aws_lambda_function.visual_asset_generator.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Visual Asset Generator Lambda function"
  value       = aws_lambda_function.visual_asset_generator.arn
}

output "lambda_function_url" {
  description = "Function URL for the Visual Asset Generator Lambda"
  value       = aws_lambda_function_url.visual_asset_generator_url.function_url
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role" 
  value       = aws_iam_role.visual_asset_generator_role.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.visual_asset_generator_logs.name
}