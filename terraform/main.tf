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

  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
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

  depends_on = [module.iam, module.bedrock]
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

  # Lambda ARNs for action groups
  image_analysis_lambda_arn         = module.image_analysis.lambda_function_arn
  data_enrichment_lambda_arn        = module.data_enrichment.lambda_function_arn
  cultural_intelligence_lambda_arn  = module.cultural_intelligence.lambda_function_arn
  campaign_generation_lambda_arn    = ""
  voice_of_market_lambda_arn        = ""
  lokalize_lambda_arn               = ""

  depends_on = [module.iam, module.image_analysis, module.data_enrichment, module.cultural_intelligence]
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

  depends_on = [module.lambda]
}

# Knowledge Bases Module for cross-cultural adaptation
module "knowledge_bases" {
  source = "./modules/knowledge_bases"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

# Cultural Intelligence Module for knowledge base interaction
# Cultural Intelligence Lambda Module
module "cultural_intelligence" {
  source = "./modules/cultural_intelligence"

  project_name                    = var.project_name
  environment                     = var.environment
  s3_knowledge_base_bucket_name   = module.knowledge_bases.knowledge_base_documents_bucket_name
  cultural_intelligence_kb_arn    = ""
  market_intelligence_kb_arn      = ""
}
