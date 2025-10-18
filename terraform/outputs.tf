# Root Terraform Outputs

# S3 Bucket outputs for use by other resources
output "s3_bucket_name" {
  description = "Name of the S3 bucket for image storage"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for IAM policies"
  value       = module.s3.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.s3.bucket_domain_name
}

# API Gateway outputs
output "api_gateway_url" {
  description = "Full URL of the API Gateway"
  value       = module.api_gateway.api_gateway_url
}

output "presigned_url_endpoint" {
  description = "Full URL for presigned URL generation"
  value       = module.api_gateway.presigned_url_route
}

output "upload_status_endpoint" {
  description = "Base URL for upload status checking"
  value       = module.api_gateway.upload_status_route
}

output "campaign_generation_endpoint" {
  description = "POST endpoint for campaign generation (tier-1)"
  value       = "${module.api_gateway.api_gateway_url}/api/campaigns/tier-1"
}

output "uploads_presigned_url_endpoint" {
  description = "POST endpoint for upload presigned URL generation"
  value       = "${module.api_gateway.api_gateway_url}/api/uploads/presigned-url"
}

output "uploads_status_endpoint" {
  description = "GET endpoint for upload status"
  value       = "${module.api_gateway.api_gateway_url}/api/uploads/{uploadId}"
}

output "assets_generation_post_endpoint" {
  description = "POST endpoint for asset generation (triggers SQS)"
  value       = "${module.api_gateway.api_gateway_url}/api/assets/"
}

output "assets_status_get_endpoint" {
  description = "GET endpoint for asset generation status"
  value       = "${module.api_gateway.api_gateway_url}/api/assets/{request_id}"
}

# Lambda outputs
output "upload_handler_function_name" {
  description = "Name of the upload handler Lambda function"
  value       = module.lambda.upload_handler_function_name
}

output "intent_parser_function_name" {
  description = "Name of the intent parser Lambda function"
  value       = module.lambda.intent_parser_function_name
}

output "image_generation_status_lambda_arn" {
  description = "ARN of the image generation status Lambda function"
  value       = module.lambda.image_generation_status_lambda_arn
}

# SQS outputs
output "image_generation_queue_arn" {
  description = "ARN of the image generation SQS queue"
  value       = module.sqs.image_generation_queue_arn
}