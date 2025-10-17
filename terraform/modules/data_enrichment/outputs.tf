# Data Enrichment Module Outputs

output "lambda_function_name" {
  description = "Name of the data enrichment Lambda function"
  value       = aws_lambda_function.data_enrichment.function_name
}

output "lambda_function_arn" {
  description = "ARN of the data enrichment Lambda function"
  value       = aws_lambda_function.data_enrichment.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the data enrichment Lambda function"
  value       = aws_lambda_function.data_enrichment.invoke_arn
}

output "dynamodb_table_name" {
  description = "Name of the data enrichment DynamoDB table"
  value       = aws_dynamodb_table.data_enrichment.name
}

output "dynamodb_table_arn" {
  description = "ARN of the data enrichment DynamoDB table"
  value       = aws_dynamodb_table.data_enrichment.arn
}