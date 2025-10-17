# Create zip file for Lambda function
data "archive_file" "visual_asset_generator_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda/visual_asset_generator"
  output_path = "${path.module}/../../../lambda/visual_asset_generator.zip"
}

# IAM role for Lambda function
resource "aws_iam_role" "visual_asset_generator_role" {
  name = "${var.project_name}-${var.environment}-visual-asset-generator-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda function
resource "aws_iam_role_policy" "visual_asset_generator_policy" {
  name = "${var.project_name}-${var.environment}-visual-asset-generator-policy"
  role = aws_iam_role.visual_asset_generator_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:GetModel",
          "bedrock:ListModels"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-image-generator-v1",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.nova-reel-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_assets_bucket}/*",
          "arn:aws:s3:::${var.s3_assets_bucket}/generated-assets/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.s3_assets_bucket}"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_table_name}"
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "visual_asset_generator" {
  filename         = data.archive_file.visual_asset_generator_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-visual-asset-generator"
  role            = aws_iam_role.visual_asset_generator_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.visual_asset_generator_zip.output_base64sha256
  runtime         = "python3.12"
  timeout         = 900  # 15 minutes for asset generation
  memory_size     = 2048  # Higher memory for image processing

  environment {
    variables = {
      S3_ASSETS_BUCKET       = var.s3_assets_bucket
      DYNAMODB_TABLE_NAME    = var.dynamodb_table_name
      PROJECT_NAME           = var.project_name
      ENVIRONMENT            = var.environment
      REGION                 = var.aws_region
    }
  }

  depends_on = [
    aws_iam_role_policy.visual_asset_generator_policy,
    data.archive_file.visual_asset_generator_zip
  ]

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "visual_asset_generator_logs" {
  name              = "/aws/lambda/${aws_lambda_function.visual_asset_generator.function_name}"
  retention_in_days = 14

  tags = var.tags
}

# Lambda permission for Bedrock Agent to invoke function
resource "aws_lambda_permission" "bedrock_invoke_visual_asset_generator" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.visual_asset_generator.function_name
  principal     = "bedrock.amazonaws.com"
}

# Lambda function URL (optional - for direct testing)
resource "aws_lambda_function_url" "visual_asset_generator_url" {
  function_name      = aws_lambda_function.visual_asset_generator.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST", "GET"]
    allow_headers     = ["date", "keep-alive", "content-type"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}