output "image_analysis_lambda_arn" {
  value = aws_lambda_function.image_analysis.arn
}

output "data_enrichment_lambda_arn" {
  value = aws_lambda_function.data_enrichment.arn
}

output "cultural_intelligence_lambda_arn" {
  value = aws_lambda_function.cultural_intelligence.arn
}

output "intent_parser_lambda_arn" {
  value = aws_lambda_function.intent_parser.arn
}

output "generate_images_lambda_arn" {
  value = aws_lambda_function.generate_images.arn
}

output "image_generation_status_lambda_arn" {
  value = aws_lambda_function.image_generation_status.arn
}

output "image_analysis_lambda_role_arn" {
  value = aws_iam_role.lambda_image_analysis_role.arn
}

output "data_enrichment_lambda_role_arn" {
  value = aws_iam_role.lambda_data_enrichment_role.arn
}

output "cultural_intelligence_lambda_role_arn" {
  value = aws_iam_role.lambda_cultural_intelligence_role.arn
}

output "intent_parser_lambda_role_arn" {
  value = aws_iam_role.lambda_intent_parser_role.arn
}

output "generate_images_lambda_role_arn" {
  value = aws_iam_role.lambda_generate_images_role.arn
}

output "image_generation_status_lambda_role_arn" {
  value = aws_iam_role.lambda_image_generation_status_role.arn
}

output "upload_handler_lambda_arn" {
  value = aws_lambda_function.upload_handler.arn
}

output "upload_handler_function_name" {
  value = aws_lambda_function.upload_handler.function_name
}

output "intent_parser_function_name" {
  value = aws_lambda_function.intent_parser.function_name
}

output "image_generation_status_function_name" {
  value = aws_lambda_function.image_generation_status.function_name
}
