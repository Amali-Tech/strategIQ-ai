# Main Terraform Configuration for AWS AI Hackathon

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# IAM Module - Must be first as other modules depend on roles
module "iam" {
  source = "./modules/iam"
  
  project_name          = var.project_name
  environment          = var.environment
  s3_bucket_arn        = module.s3.bucket_arn
  dynamodb_table_arns  = module.dynamodb.table_arns
  dynamodb_stream_arns = module.dynamodb.stream_arns
  sqs_queue_arns       = module.sqs.queue_arns
  
  tags = local.common_tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
  
  tags = local.common_tags
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"
  
  project_name = var.project_name
  environment  = var.environment
  
  tags = local.common_tags
}

# SQS Module
module "sqs" {
  source = "./modules/sqs"
  
  project_name = var.project_name
  environment  = var.environment
  
  tags = local.common_tags
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"
  
  project_name                     = var.project_name
  environment                     = var.environment
  lambda_image_analysis_role_arn  = module.iam.lambda_image_analysis_role_arn
  lambda_campaign_role_arn        = module.iam.lambda_campaign_role_arn
  lambda_api_role_arn             = module.iam.lambda_api_role_arn
  s3_bucket_name                  = module.s3.bucket_name
  product_analysis_table_name     = module.dynamodb.product_analysis_table_name
  enriched_data_table_name        = module.dynamodb.enriched_data_table_name
  campaign_sqs_queue_url          = module.sqs.campaign_generation_queue_url
  youtube_api_key                 = var.youtube_api_key
  bedrock_model_id                = var.bedrock_model_id
  
  tags = local.common_tags
  
  depends_on = [module.iam, module.s3, module.dynamodb, module.sqs]
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api-gateway"
  
  project_name                           = var.project_name
  environment                           = var.environment
  generate_presigned_url_lambda_invoke_arn = module.lambda.api_lambda_integrations.generate_presigned_url.invoke_arn
  get_status_lambda_invoke_arn          = module.lambda.api_lambda_integrations.get_status.invoke_arn
  
  tags = local.common_tags
  
  depends_on = [module.lambda]
}

# EventBridge Module
module "eventbridge" {
  source = "./modules/eventbridge"
  
  project_name                    = var.project_name
  environment                    = var.environment
  eventbridge_pipes_role_arn     = module.iam.eventbridge_pipes_role_arn
  product_analysis_stream_arn    = module.dynamodb.product_analysis_stream_arn
  enriched_data_stream_arn       = module.dynamodb.enriched_data_stream_arn
  campaign_data_stream_arn       = module.dynamodb.campaign_data_stream_arn
  enrichment_lambda_arn          = module.lambda.enrichment_function_arn
  campaign_generator_lambda_arn  = module.lambda.campaign_generator_function_arn
  campaign_generator_lambda_name = module.lambda.campaign_generator_function_name
  campaign_sqs_queue_arn         = module.sqs.campaign_generation_queue_arn
  
  tags = local.common_tags
  
  depends_on = [module.iam, module.dynamodb, module.lambda, module.sqs]
}

# Local values for common tags
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "degenerals-infra"
  }
}