# Lambda Module
# This module manages lambda resources for the AWS AI Hackathon project

# Create the proper directory structure for the lambda layer using local-exec
resource "null_resource" "create_layer_structure" {
  triggers = {
    # Trigger recreation when python directory contents change
    python_hash = sha256(join("", [for f in fileset("${path.root}/../python", "**") : filesha256("${path.root}/../python/${f}")]))
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      cd "${path.root}/.."
      rm -f lambda_layer.zip
      zip -r lambda_layer.zip python/ \
        -x "python/**/__pycache__/**" \
           "python/**/*.pyc" \
           "python/**/.pytest_cache/**" \
           "python/**/tests/**" \
           "python/**/.DS_Store"
    EOT
  }
}

# Lambda Layer for shared dependencies
resource "aws_lambda_layer_version" "shared_dependencies" {
  filename            = "${path.root}/../lambda_layer.zip"
  layer_name          = "${var.project_name}-${var.environment}-shared-dependencies"
  source_code_hash    = null_resource.create_layer_structure.triggers.python_hash
  
  compatible_runtimes = ["python3.11", "python3.12"]
  description         = "Shared dependencies for all Lambda functions"
  
  depends_on = [null_resource.create_layer_structure]
}

# Create ZIP files for each Lambda function
data "archive_file" "analyze_image_lambda" {
  type        = "zip"
  source_file = "${path.module}/scripts/analyse_image_lambda.py"
  output_path = "${path.module}/zips/analyze_image_lambda.zip"
}

data "archive_file" "generate_presigned_url_lambda" {
  type        = "zip"
  source_file = "${path.module}/scripts/generate_pre-singed_url_lambda.py"
  output_path = "${path.module}/zips/generate_presigned_url_lambda.zip"
}

data "archive_file" "enrichment_lambda" {
  type        = "zip"
  source_file = "${path.module}/scripts/enrichment_lambda.py"
  output_path = "${path.module}/zips/enrichment_lambda.zip"
}

data "archive_file" "campaign_generator_lambda" {
  type        = "zip"
  source_file = "${path.module}/scripts/campaign_generator_lambda.py"
  output_path = "${path.module}/zips/campaign_generator_lambda.zip"
}

data "archive_file" "get_status_lambda" {
  type        = "zip"
  source_file = "${path.module}/scripts/get_status_lambda.py"
  output_path = "${path.module}/zips/get_status_lambda.zip"
}

# Lambda Function: Analyze Image (triggered by S3 uploads)
resource "aws_lambda_function" "analyze_image" {
  filename         = data.archive_file.analyze_image_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-analyze-image"
  role            = var.lambda_image_analysis_role_arn
  handler         = "analyse_image_lambda.lambda_handler"
  source_code_hash = data.archive_file.analyze_image_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 1024
  
  layers = [aws_lambda_layer_version.shared_dependencies.arn]
  
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.product_analysis_table_name
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_lambda_layer_version.shared_dependencies]
}

# Lambda Function: Generate Presigned URL (API Gateway)
resource "aws_lambda_function" "generate_presigned_url" {
  filename         = data.archive_file.generate_presigned_url_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-generate-presigned-url"
  role            = var.lambda_api_role_arn
  handler         = "generate_pre-singed_url_lambda.lambda_handler"
  source_code_hash = data.archive_file.generate_presigned_url_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256
  
  layers = [aws_lambda_layer_version.shared_dependencies.arn]
  
  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_lambda_layer_version.shared_dependencies]
}

# Lambda Function: Data Enrichment (EventBridge Pipes)
resource "aws_lambda_function" "enrichment" {
  filename         = data.archive_file.enrichment_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-enrichment"
  role            = var.lambda_image_analysis_role_arn
  handler         = "enrichment_lambda.lambda_handler"
  source_code_hash = data.archive_file.enrichment_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512
  
  layers = [aws_lambda_layer_version.shared_dependencies.arn]
  
  environment {
    variables = {
      YOUTUBE_API_KEY           = var.youtube_api_key
      ENRICHED_TABLE_NAME      = var.enriched_data_table_name
      CAMPAIGN_SQS_QUEUE_URL   = var.campaign_sqs_queue_url
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_lambda_layer_version.shared_dependencies]
}

# Lambda Function: Campaign Generator (Bedrock)
resource "aws_lambda_function" "campaign_generator" {
  filename         = data.archive_file.campaign_generator_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-campaign-generator"
  role            = var.lambda_campaign_role_arn
  handler         = "campaign_generator_lambda.lambda_handler"
  source_code_hash = data.archive_file.campaign_generator_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 600
  memory_size     = 1024
  
  layers = [aws_lambda_layer_version.shared_dependencies.arn]
  
  environment {
    variables = {
      DYNAMODB_TABLE     = var.enriched_data_table_name
      BEDROCK_MODEL_ID   = var.bedrock_model_id
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_lambda_layer_version.shared_dependencies]
}

# Lambda Function: Get Status (API Gateway)
resource "aws_lambda_function" "get_status" {
  filename         = data.archive_file.get_status_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-get-status"
  role            = var.lambda_api_role_arn
  handler         = "get_status_lambda.lambda_handler"
  source_code_hash = data.archive_file.get_status_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256
  
  layers = [aws_lambda_layer_version.shared_dependencies.arn]
  
  environment {
    variables = {
      ANALYSIS_TABLE     = var.product_analysis_table_name
      ENRICHED_TABLE     = var.enriched_data_table_name
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_lambda_layer_version.shared_dependencies]
}

# S3 Event Notification for Image Analysis Lambda
resource "aws_s3_bucket_notification" "image_upload" {
  bucket = var.s3_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.analyze_image.arn
    events             = ["s3:ObjectCreated:*"]
    filter_prefix      = "uploads/"
    filter_suffix      = ".jpg"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.analyze_image.arn
    events             = ["s3:ObjectCreated:*"]
    filter_prefix      = "uploads/"
    filter_suffix      = ".jpeg"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.analyze_image.arn
    events             = ["s3:ObjectCreated:*"]
    filter_prefix      = "uploads/"
    filter_suffix      = ".png"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.analyze_image.arn
    events             = ["s3:ObjectCreated:*"]
    filter_prefix      = "uploads/"
    filter_suffix      = ".jfif"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.analyze_image.arn
    events             = ["s3:ObjectCreated:*"]
    filter_prefix      = "uploads/"
    filter_suffix      = ".webp"
  }

  depends_on = [aws_lambda_permission.s3_invoke_analyze_image]
}

# Lambda Permission for S3 to invoke the analyze image function
resource "aws_lambda_permission" "s3_invoke_analyze_image" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analyze_image.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_bucket_name}"
}

# Lambda Permission for API Gateway to invoke presigned URL function
resource "aws_lambda_permission" "api_gateway_invoke_presigned_url" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generate_presigned_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*/*/*"
}

# Lambda Permission for API Gateway to invoke get status function
resource "aws_lambda_permission" "api_gateway_invoke_get_status" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*/*/*"
}

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}
