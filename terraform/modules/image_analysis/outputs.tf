output "lambda_function_arn" {
  description = "ARN of the image analysis Lambda function"
  value       = aws_lambda_function.image_analysis.arn
}

output "lambda_function_name" {
  description = "Name of the image analysis Lambda function"
  value       = aws_lambda_function.image_analysis.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for image analysis"
  value       = aws_dynamodb_table.image_analysis.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for image analysis"
  value       = aws_dynamodb_table.image_analysis.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.image_analysis_role.arn
}