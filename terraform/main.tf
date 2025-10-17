# Main Terraform configuration

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

  project_name                  = var.project_name
  environment                   = var.environment
  s3_bucket_arn                = module.s3.bucket_arn
  campaign_tracking_policy_arn = module.campaign_tracking.campaign_tracking_policy_arn

  depends_on = [module.campaign_tracking]
}

# Lambda Module for upload handler and intent parser functions
module "lambda" {
  source = "./modules/lambda"

  project_name               = var.project_name
  environment                = var.environment
  s3_bucket_name            = module.s3.bucket_name
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  supervisor_agent_id       = module.bedrock.supervisor_agent_id
  supervisor_agent_alias_id = var.supervisor_agent_alias_id_override != "" ? var.supervisor_agent_alias_id_override : module.bedrock.supervisor_agent_alias_id
  campaign_status_table_name = module.campaign_tracking.campaign_status_table_name
  campaign_events_bus_name   = module.campaign_tracking.campaign_events_bus_name
  visual_asset_queue_arn     = module.campaign_tracking.visual_asset_queue_arn

  depends_on = [module.iam, module.bedrock, module.campaign_tracking]
}

# Bedrock Module for AI agent orchestration
module "bedrock" {
  source = "./modules/bedrock"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # Bedrock model configuration
  bedrock_model_id                    = var.bedrock_model_id
  bedrock_agent_inference_profile_arn = var.bedrock_agent_inference_profile_arn
  cultural_intelligence_kb_id         = var.cultural_intelligence_kb_id

  # Lambda ARNs for action groups
  image_analysis_lambda_arn         = module.image_analysis.lambda_function_arn
  data_enrichment_lambda_arn        = module.data_enrichment.lambda_function_arn
  cultural_intelligence_lambda_arn  = module.cultural_intelligence.lambda_function_arn
  sentiment_analysis_lambda_arn     = module.sentiment_analysis.sentiment_analysis_lambda_arn
  visual_asset_generator_lambda_arn = module.visual_asset_generator.lambda_function_arn
  campaign_generation_lambda_arn    = ""
  voice_of_market_lambda_arn        = ""
  lokalize_lambda_arn               = ""

  depends_on = [module.iam, module.image_analysis, module.data_enrichment, module.cultural_intelligence, module.visual_asset_generator]
}

# Image Analysis Module for product image analysis
module "image_analysis" {
  source = "./modules/image_analysis"

  project_name    = var.project_name
  environment     = var.environment
  s3_bucket_name  = module.s3.bucket_name

  depends_on = [module.s3]
}

# Data Enrichment Module for YouTube API integration
module "data_enrichment" {
  source = "./modules/data_enrichment"

  project_name    = var.project_name
  environment     = var.environment
  youtube_api_key = var.youtube_api_key

  depends_on = [module.iam]
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

# Knowledge Bases Module for cross-cultural adaptation
# Commented out - Knowledge base will be created manually
# module "knowledge_bases" {
#   source = "./modules/knowledge_bases"
#
#   project_name = var.project_name
#   environment  = var.environment
#   aws_region   = var.aws_region
# }

# Campaign Tracking Module for async visual asset generation
module "campaign_tracking" {
  source = "./modules/campaign-tracking"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

# Cultural Intelligence Lambda Module
module "cultural_intelligence" {
  source = "./modules/cultural_intelligence"

  project_name                    = var.project_name
  environment                     = var.environment
  s3_knowledge_base_bucket_name   = "${var.project_name}-${var.environment}-knowledge-base-docs"  # Hardcoded since KB is manual
  cultural_intelligence_kb_id     = var.cultural_intelligence_kb_id
  cultural_intelligence_kb_arn    = var.cultural_intelligence_kb_id != "" ? "arn:aws:bedrock:${var.aws_region}:*:knowledge-base/${var.cultural_intelligence_kb_id}" : ""
  market_intelligence_kb_id       = var.cultural_intelligence_kb_id  # Using same KB for both for now
  market_intelligence_kb_arn      = var.cultural_intelligence_kb_id != "" ? "arn:aws:bedrock:${var.aws_region}:*:knowledge-base/${var.cultural_intelligence_kb_id}" : ""
}

# Sentiment Analysis Module for market sentiment and action items
module "sentiment_analysis" {
  source = "./modules/sentiment_analysis"

  project_name         = var.project_name
  aws_region           = var.aws_region
  dynamodb_table_name  = module.cultural_intelligence.dynamodb_table_name
  dynamodb_table_arn   = module.cultural_intelligence.dynamodb_table_arn
  enable_api_gateway   = false  # Will be enabled after API Gateway is created
  api_gateway_execution_arn = ""
  enable_bedrock_agent = false  # Will be enabled when Bedrock agent is updated
  bedrock_agent_arn    = ""

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Module      = "sentiment-analysis"
  }

  depends_on = [module.cultural_intelligence]
}

# Visual Asset Generator Module for creating video scripts, thumbnails, and social media content
module "visual_asset_generator" {
  source = "./modules/visual_asset_generator"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  s3_assets_bucket     = module.s3.bucket_name
  dynamodb_table_name  = module.cultural_intelligence.dynamodb_table_name

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Module      = "visual-asset-generator"
  }

  depends_on = [module.s3, module.cultural_intelligence]
}
