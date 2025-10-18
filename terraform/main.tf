module "s3" {
  source         = "./modules/s3"
  project_name   = var.project_name
  environment    = var.environment
  days           = 30
  allowed_origins = var.s3_allowed_origins
}

module "dynamodb" {
  source                = "./modules/dynamodb"
  project_name          = var.project_name
  environment           = var.environment
  products_table_name   = var.products_table_name
  generated_images_table_name = var.generated_images_table_name
}

module "sqs" {
  source                      = "./modules/sqs"
  image_generation_queue_name = var.image_generation_queue_name
  generate_images_lambda_arn  = module.lambda.generate_images_lambda_arn
}

module "lambda" {
  source = "./modules/lambda"

  project_root        = abspath(path.root)
  lambda_image_analysis_function_name      = var.lambda_image_analysis_function_name
  lambda_data_enrichment_function_name     = var.lambda_data_enrichment_function_name
  lambda_cultural_intelligence_function_name = var.lambda_cultural_intelligence_function_name
  lambda_intent_parser_function_name       = var.lambda_intent_parser_function_name
  lambda_generate_images_function_name     = var.lambda_generate_images_function_name
  lambda_image_generation_status_function_name = var.lambda_image_generation_status_function_name

  lambda_upload_handler_function_name = var.lambda_upload_handler_function_name

  dynamodb_table_name = module.dynamodb.products_table_name
  s3_bucket_name      = module.s3.bucket_name
  bedrock_agent_id    = var.bedrock_agent_id
  bedrock_agent_alias_id = var.bedrock_agent_alias_id
  bedrock_nova_canvas_model_id = var.bedrock_nova_canvas_model_id
  api_key_youtube     = var.youtube_api_key
  api_key_other       = var.api_key_other
}

module "api_gateway" {
  source = "./modules/api-gateway"

  project_name = var.project_name
  environment  = var.environment
  s3_bucket_name = module.s3.bucket_name
  cors_allowed_origins = var.s3_allowed_origins

  upload_handler_invoke_arn = module.lambda.upload_handler_lambda_arn
  upload_handler_function_name = module.lambda.upload_handler_function_name
  intent_parser_invoke_arn = module.lambda.intent_parser_lambda_arn
  intent_parser_function_name = module.lambda.intent_parser_function_name
  assets_sqs_arn = module.sqs.image_generation_queue_arn
  image_generation_status_invoke_arn = module.lambda.image_generation_status_lambda_arn
  image_generation_status_function_name = module.lambda.image_generation_status_function_name
}

resource "local_file" "terraform_outputs_json" {
  filename = "terraform-outputs.json"
  content  = jsonencode({
    s3 = {
      bucket_name = module.s3.bucket_name
      bucket_arn = module.s3.bucket_arn
      bucket_domain_name = module.s3.bucket_domain_name
    }
    dynamodb = {
      products_table_name = module.dynamodb.products_table_name
      generated_images_table_name = module.dynamodb.generated_images_table_name
    }
    sqs = {
      image_generation_queue_arn = module.sqs.image_generation_queue_arn
      image_generation_queue_url = module.sqs.image_generation_queue_url
    }
    lambda = {
      image_analysis_lambda_arn = module.lambda.image_analysis_lambda_arn
      data_enrichment_lambda_arn = module.lambda.data_enrichment_lambda_arn
      cultural_intelligence_lambda_arn = module.lambda.cultural_intelligence_lambda_arn
      intent_parser_lambda_arn = module.lambda.intent_parser_lambda_arn
      generate_images_lambda_arn = module.lambda.generate_images_lambda_arn
      image_generation_status_lambda_arn = module.lambda.image_generation_status_lambda_arn
    }
    api_gateway = {
      api_gateway_url = module.api_gateway.api_gateway_url
      campaign_generation_endpoint = "${module.api_gateway.api_gateway_url}/api/campaigns/tier-1"
      uploads_presigned_url_endpoint = "${module.api_gateway.api_gateway_url}/api/uploads/presigned-url"
      uploads_status_endpoint = "${module.api_gateway.api_gateway_url}/api/uploads/{uploadId}"
      assets_generation_post_endpoint = "${module.api_gateway.api_gateway_url}/api/assets/"
      assets_status_get_endpoint = "${module.api_gateway.api_gateway_url}/api/assets/{request_id}"
    }
  })
}
