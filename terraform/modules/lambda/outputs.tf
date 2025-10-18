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

output "campaign_status_function_name" {
  description = "Name of the campaign status Lambda function"
  value       = aws_lambda_function.campaign_status.function_name
}

output "campaign_status_function_arn" {
  description = "ARN of the campaign status Lambda function"
  value       = aws_lambda_function.campaign_status.arn
}

output "campaign_status_invoke_arn" {
  description = "Invoke ARN of the campaign status Lambda function"
  value       = aws_lambda_function.campaign_status.invoke_arn
}

# Action Group Lambda Function Outputs

output "data_enrichment_function_name" {
  description = "Name of the data enrichment Lambda function (action group)"
  value       = aws_lambda_function.data_enrichment.function_name
}

output "data_enrichment_function_arn" {
  description = "ARN of the data enrichment Lambda function"
  value       = aws_lambda_function.data_enrichment.arn
}

output "image_analysis_function_name" {
  description = "Name of the image analysis Lambda function (action group)"
  value       = aws_lambda_function.image_analysis.function_name
}

output "image_analysis_function_arn" {
  description = "ARN of the image analysis Lambda function"
  value       = aws_lambda_function.image_analysis.arn
}

output "cultural_intelligence_function_name" {
  description = "Name of the cultural intelligence Lambda function (action group)"
  value       = aws_lambda_function.cultural_intelligence.function_name
}

output "cultural_intelligence_function_arn" {
  description = "ARN of the cultural intelligence Lambda function"
  value       = aws_lambda_function.cultural_intelligence.arn
}

output "sentiment_analysis_function_name" {
  description = "Name of the sentiment analysis Lambda function (action group)"
  value       = aws_lambda_function.sentiment_analysis.function_name
}

output "sentiment_analysis_function_arn" {
  description = "ARN of the sentiment analysis Lambda function"
  value       = aws_lambda_function.sentiment_analysis.arn
}

output "visual_asset_generator_function_name" {
  description = "Name of the visual asset generator Lambda function (action group)"
  value       = aws_lambda_function.visual_asset_generator.function_name
}

output "visual_asset_generator_function_arn" {
  description = "ARN of the visual asset generator Lambda function"
  value       = aws_lambda_function.visual_asset_generator.arn
}
