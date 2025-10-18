output "lambda_function_arn" {
  description = "ARN of the Cultural Intelligence Lambda function"
  value       = aws_lambda_function.cultural_intelligence.arn
}

output "lambda_function_name" {
  description = "Name of the Cultural Intelligence Lambda function"
  value       = aws_lambda_function.cultural_intelligence.function_name
}

output "lambda_function_invoke_arn" {
  description = "Invoke ARN of the Cultural Intelligence Lambda function"
  value       = aws_lambda_function.cultural_intelligence.invoke_arn
}

output "dynamodb_table_name" {
  description = "Name of the Cultural Intelligence DynamoDB table"
  value       = aws_dynamodb_table.cultural_intelligence.name
}

output "dynamodb_table_arn" {
  description = "ARN of the Cultural Intelligence DynamoDB table"
  value       = aws_dynamodb_table.cultural_intelligence.arn
}