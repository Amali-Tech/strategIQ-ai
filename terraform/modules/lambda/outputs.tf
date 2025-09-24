# Lambda Module Outputs

# Lambda Layer
output "lambda_layer_arn" {
  description = "ARN of the shared Lambda layer"
  value       = aws_lambda_layer_version.shared_dependencies.arn
}

output "lambda_layer_version" {
  description = "Version of the shared Lambda layer"
  value       = aws_lambda_layer_version.shared_dependencies.version
}

# Individual Lambda Function ARNs
output "analyze_image_function_arn" {
  description = "ARN of the analyze image Lambda function"
  value       = aws_lambda_function.analyze_image.arn
}

output "generate_presigned_url_function_arn" {
  description = "ARN of the generate presigned URL Lambda function"
  value       = aws_lambda_function.generate_presigned_url.arn
}

output "enrichment_function_arn" {
  description = "ARN of the enrichment Lambda function"
  value       = aws_lambda_function.enrichment.arn
}

output "campaign_generator_function_arn" {
  description = "ARN of the campaign generator Lambda function"
  value       = aws_lambda_function.campaign_generator.arn
}

output "get_status_function_arn" {
  description = "ARN of the get status Lambda function"
  value       = aws_lambda_function.get_status.arn
}

# Individual Lambda Function Names
output "analyze_image_function_name" {
  description = "Name of the analyze image Lambda function"
  value       = aws_lambda_function.analyze_image.function_name
}

output "generate_presigned_url_function_name" {
  description = "Name of the generate presigned URL Lambda function"
  value       = aws_lambda_function.generate_presigned_url.function_name
}

output "enrichment_function_name" {
  description = "Name of the enrichment Lambda function"
  value       = aws_lambda_function.enrichment.function_name
}

output "campaign_generator_function_name" {
  description = "Name of the campaign generator Lambda function"
  value       = aws_lambda_function.campaign_generator.function_name
}

output "get_status_function_name" {
  description = "Name of the get status Lambda function"
  value       = aws_lambda_function.get_status.function_name
}

# Consolidated outputs for easier consumption
output "function_arns" {
  description = "Map of all Lambda function ARNs"
  value = {
    analyze_image          = aws_lambda_function.analyze_image.arn
    generate_presigned_url = aws_lambda_function.generate_presigned_url.arn
    enrichment            = aws_lambda_function.enrichment.arn
    campaign_generator    = aws_lambda_function.campaign_generator.arn
    get_status           = aws_lambda_function.get_status.arn
  }
}

output "function_names" {
  description = "Map of all Lambda function names"
  value = {
    analyze_image          = aws_lambda_function.analyze_image.function_name
    generate_presigned_url = aws_lambda_function.generate_presigned_url.function_name
    enrichment            = aws_lambda_function.enrichment.function_name
    campaign_generator    = aws_lambda_function.campaign_generator.function_name
    get_status           = aws_lambda_function.get_status.function_name
  }
}

# API Gateway Integration outputs
output "api_lambda_integrations" {
  description = "Lambda functions for API Gateway integration"
  value = {
    generate_presigned_url = {
      function_name = aws_lambda_function.generate_presigned_url.function_name
      invoke_arn   = aws_lambda_function.generate_presigned_url.invoke_arn
    }
    get_status = {
      function_name = aws_lambda_function.get_status.function_name
      invoke_arn   = aws_lambda_function.get_status.invoke_arn
    }
  }
}
