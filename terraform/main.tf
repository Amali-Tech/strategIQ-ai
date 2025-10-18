# Main Terraform configuration
# Deploys Lambda action groups + utilities, IAM roles, S3 bucket, and API Gateway

# S3 Module for image storage
module "s3" {
  source = "./modules/s3"

  project_name    = var.project_name
  environment     = var.environment
  days            = 30 # Default to 30 days for lifecycle
  allowed_origins = var.s3_allowed_origins
}

# IAM Module for Lambda execution roles and policies
module "iam" {
  source = "./modules/iam"

  project_name    = var.project_name
  environment     = var.environment
  s3_bucket_arn  = module.s3.bucket_arn
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
}

# Lambda Module - Deploys all action group handlers + utility functions
module "lambda" {
  source = "./modules/lambda"

  project_name               = var.project_name
  environment                = var.environment
  s3_bucket_name            = module.s3.bucket_name
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  image_analysis_role_arn   = module.image_analysis.lambda_role_arn
  supervisor_agent_id       = "PLACEHOLDER_AGENT_ID"
  supervisor_agent_alias_id = "PLACEHOLDER_ALIAS_ID"
  campaign_status_table_name = ""
  campaign_events_bus_name   = ""
  visual_asset_queue_arn     = ""

  depends_on = [module.iam, module.image_analysis]
}

# API Gateway Module for upload and campaign endpoints
module "api_gateway" {
  source = "./modules/api-gateway"

  project_name                   = var.project_name
  environment                    = var.environment
  s3_bucket_name                = module.s3.bucket_name
  cors_allowed_origins          = var.s3_allowed_origins
  upload_handler_invoke_arn     = module.lambda.upload_handler_invoke_arn
  upload_handler_function_name  = module.lambda.upload_handler_function_name
  intent_parser_invoke_arn      = module.lambda.intent_parser_invoke_arn
  intent_parser_function_name   = module.lambda.intent_parser_function_name
  campaign_status_invoke_arn    = module.lambda.campaign_status_invoke_arn
  campaign_status_function_name = module.lambda.campaign_status_function_name

  depends_on = [module.lambda]
}

# Image Analysis Module - Dedicated IAM role and DynamoDB for image analysis
module "image_analysis" {
  source = "./modules/image_analysis"

  project_name    = var.project_name
  environment     = var.environment
  s3_bucket_name = module.s3.bucket_name

  depends_on = [module.s3]
}

