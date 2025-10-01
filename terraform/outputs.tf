# Root-level outputs for the AWS AI Hackathon infrastructure

# API Gateway outputs
output "api_gateway_invoke_url" {
  description = "Base URL of the HTTP API Gateway"
  value       = module.api_gateway.api_gateway_invoke_url
}

output "all_endpoints" {
  description = "All available API endpoints"
  value       = module.api_gateway.all_endpoints
}

output "presigned_url_endpoint" {
  description = "Presigned URL generation endpoint"
  value       = module.api_gateway.presigned_url_endpoint
}

output "status_endpoint" {
  description = "Status check endpoint URL"
  value       = module.api_gateway.status_endpoint
}

# S3 bucket name
output "s3_bucket_name" {
  description = "Name of the S3 bucket for image storage"
  value       = module.s3.bucket_name
}

# DynamoDB table names
output "dynamodb_tables" {
  description = "Names of all DynamoDB tables"
  value = {
    product_analysis   = module.dynamodb.product_analysis_table_name
    enriched_data     = module.dynamodb.enriched_data_table_name
    campaign_data     = module.dynamodb.campaign_data_table_name
    sentiment_analysis = module.dynamodb.sentiment_analysis_table_name
    action_items      = module.dynamodb.action_items_table_name
  }
}

# SQS queue URL
output "sqs_queue_url" {
  description = "URL of the campaign generation SQS queue"
  value       = module.sqs.campaign_generation_queue_url
}

# Lambda function names
output "lambda_functions" {
  description = "Names of all Lambda functions"
  value = {
    analyze_image        = "aws-ai-hackathon-dev-analyze-image"
    generate_presigned_url = "aws-ai-hackathon-dev-generate-presigned-url"
    enrichment          = "aws-ai-hackathon-dev-enrichment"
    campaign_generator  = "aws-ai-hackathon-dev-campaign-generator"
    get_status         = "aws-ai-hackathon-dev-get-status"
  }
}

# Lokalize Agent outputs
output "lokalize_agent" {
  description = "Lokalize Agent information"
  value = {
    agent_id       = module.lokalize_agent.agent_id
    agent_arn      = module.lokalize_agent.agent_arn
    agent_alias_id = module.lokalize_agent.agent_alias_id
    agent_alias_arn = module.lokalize_agent.agent_alias_arn
    lambda_functions = module.lokalize_agent.lambda_functions
  }
}
