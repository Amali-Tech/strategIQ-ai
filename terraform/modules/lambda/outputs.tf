# Lambda Module Outputs

output "upload_handler_function_name" {
  description = "Name of the upload handler Lambda function"
  value       = aws_lambda_function.upload_handler.function_name
}

output "upload_handler_function_arn" {
  description = "ARN of the upload handler Lambda function"
  value       = aws_lambda_function.upload_handler.arn
}

output "upload_handler_invoke_arn" {
  description = "Invoke ARN of the upload handler Lambda function"
  value       = aws_lambda_function.upload_handler.invoke_arn
}

output "intent_parser_function_name" {
  description = "Name of the intent parser Lambda function"
  value       = aws_lambda_function.intent_parser.function_name
}

output "intent_parser_function_arn" {
  description = "ARN of the intent parser Lambda function"
  value       = aws_lambda_function.intent_parser.arn
}

output "intent_parser_invoke_arn" {
  description = "Invoke ARN of the intent parser Lambda function"
  value       = aws_lambda_function.intent_parser.invoke_arn
}
