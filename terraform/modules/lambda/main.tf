resource "aws_iam_role" "lambda_image_analysis_role" {
  name = "lambda_image_analysis_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role" "lambda_data_enrichment_role" {
  name = "lambda_data_enrichment_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role" "lambda_cultural_intelligence_role" {
  name = "lambda_cultural_intelligence_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role" "lambda_intent_parser_role" {
  name = "lambda_intent_parser_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role" "lambda_generate_images_role" {
  name = "lambda_generate_images_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

resource "aws_iam_role" "lambda_image_generation_status_role" {
  name = "lambda_image_generation_status_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_lambda_function" "image_analysis" {
  function_name = var.lambda_image_analysis_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/image_analysis/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/image_analysis/handler.py")
  role          = aws_iam_role.lambda_image_analysis_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      S3_BUCKET_NAME      = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "data_enrichment" {
  function_name = var.lambda_data_enrichment_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/data_enrichment/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/data_enrichment/handler.py")
  role          = aws_iam_role.lambda_data_enrichment_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      API_KEY_YOUTUBE     = var.api_key_youtube
      S3_BUCKET_NAME      = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "cultural_intelligence" {
  function_name = var.lambda_cultural_intelligence_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/cultural_intelligence/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/cultural_intelligence/handler.py")
  role          = aws_iam_role.lambda_cultural_intelligence_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      S3_BUCKET_NAME      = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "intent_parser" {
  function_name = var.lambda_intent_parser_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/intent_parser/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/intent_parser/handler.py")
  role          = aws_iam_role.lambda_intent_parser_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME      = var.dynamodb_table_name
      S3_BUCKET_NAME           = var.s3_bucket_name
      BEDROCK_AGENT_ID         = var.bedrock_agent_id
      BEDROCK_AGENT_ALIAS_ID   = var.bedrock_agent_alias_id
      LAMBDA_IMAGE_ANALYSIS    = var.lambda_image_analysis_function_name
      LAMBDA_DATA_ENRICHMENT   = var.lambda_data_enrichment_function_name
      LAMBDA_CULTURAL_INTELLIGENCE = var.lambda_cultural_intelligence_function_name
    }
  }
}

resource "aws_lambda_function" "generate_images" {
  function_name = var.lambda_generate_images_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/generate-images/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/generate-images/handler.py")
  role          = aws_iam_role.lambda_generate_images_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME      = var.dynamodb_table_name
      S3_BUCKET_NAME           = var.s3_bucket_name
      BEDROCK_NOVA_CANVAS_MODEL_ID = var.bedrock_nova_canvas_model_id
    }
  }
}

resource "aws_lambda_function" "image_generation_status" {
  function_name = var.lambda_image_generation_status_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/image-generation-status/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/image-generation-status/handler.py")
  role          = aws_iam_role.lambda_image_generation_status_role.arn
  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
    }
  }
}

resource "aws_iam_policy" "lambda_image_analysis_policy" {
  name        = "lambda_image_analysis_policy"
  description = "Least-privilege policy for image analysis Lambda"
  policy      = data.aws_iam_policy_document.lambda_image_analysis_policy.json
}

data "aws_iam_policy_document" "lambda_image_analysis_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy_attachment" "lambda_image_analysis_attach" {
  role       = aws_iam_role.lambda_image_analysis_role.name
  policy_arn = aws_iam_policy.lambda_image_analysis_policy.arn
}

resource "aws_iam_policy" "lambda_data_enrichment_policy" {
  name        = "lambda_data_enrichment_policy"
  description = "Least-privilege policy for data enrichment Lambda"
  policy      = data.aws_iam_policy_document.lambda_data_enrichment_policy.json
}

data "aws_iam_policy_document" "lambda_data_enrichment_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy_attachment" "lambda_data_enrichment_attach" {
  role       = aws_iam_role.lambda_data_enrichment_role.name
  policy_arn = aws_iam_policy.lambda_data_enrichment_policy.arn
}

resource "aws_iam_policy" "lambda_cultural_intelligence_policy" {
  name        = "lambda_cultural_intelligence_policy"
  description = "Least-privilege policy for cultural intelligence Lambda"
  policy      = data.aws_iam_policy_document.lambda_cultural_intelligence_policy.json
}

data "aws_iam_policy_document" "lambda_cultural_intelligence_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy_attachment" "lambda_cultural_intelligence_attach" {
  role       = aws_iam_role.lambda_cultural_intelligence_role.name
  policy_arn = aws_iam_policy.lambda_cultural_intelligence_policy.arn
}

resource "aws_iam_policy" "lambda_intent_parser_policy" {
  name        = "lambda_intent_parser_policy"
  description = "Least-privilege policy for intent parser Lambda"
  policy      = data.aws_iam_policy_document.lambda_intent_parser_policy.json
}

data "aws_iam_policy_document" "lambda_intent_parser_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  # Add Bedrock permissions if needed
}

resource "aws_iam_role_policy_attachment" "lambda_intent_parser_attach" {
  role       = aws_iam_role.lambda_intent_parser_role.name
  policy_arn = aws_iam_policy.lambda_intent_parser_policy.arn
}

resource "aws_iam_policy" "lambda_generate_images_policy" {
  name        = "lambda_generate_images_policy"
  description = "Least-privilege policy for generate images Lambda"
  policy      = data.aws_iam_policy_document.lambda_generate_images_policy.json
}

data "aws_iam_policy_document" "lambda_generate_images_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  # Add Bedrock permissions if needed
}

resource "aws_iam_role_policy_attachment" "lambda_generate_images_attach" {
  role       = aws_iam_role.lambda_generate_images_role.name
  policy_arn = aws_iam_policy.lambda_generate_images_policy.arn
}

resource "aws_iam_policy" "lambda_image_generation_status_policy" {
  name        = "lambda_image_generation_status_policy"
  description = "Least-privilege policy for image generation status Lambda"
  policy      = data.aws_iam_policy_document.lambda_image_generation_status_policy.json
}

data "aws_iam_policy_document" "lambda_image_generation_status_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query"
    ]
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy_attachment" "lambda_image_generation_status_attach" {
  role       = aws_iam_role.lambda_image_generation_status_role.name
  policy_arn = aws_iam_policy.lambda_image_generation_status_policy.arn
}

resource "aws_lambda_function" "upload_handler" {
  function_name = var.lambda_upload_handler_function_name
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  filename      = "${var.project_root}/lambda-handlers/upload-handler/handler.py"
  source_code_hash = filebase64sha256("${var.project_root}/lambda-handlers/upload-handler/handler.py")
  role          = aws_iam_role.lambda_image_analysis_role.arn
  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name
    }
  }
}
