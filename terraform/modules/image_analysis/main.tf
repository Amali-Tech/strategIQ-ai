# DynamoDB table for storing image analysis results
resource "aws_dynamodb_table" "image_analysis" {
  name           = "${var.project_name}-${var.environment}-image-analysis"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "analysis_id"

  attribute {
    name = "analysis_id"
    type = "S"
  }



  tags = {
    Name        = "${var.project_name}-${var.environment}-image-analysis"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Store image analysis results from Rekognition"
  }
}

# Lambda function for image analysis
resource "aws_lambda_function" "image_analysis" {
  filename         = data.archive_file.image_analysis_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-image-analysis"
  role            = aws_iam_role.image_analysis_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60

  source_code_hash = data.archive_file.image_analysis_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.image_analysis.name
      S3_BUCKET_NAME      = var.s3_bucket_name
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-image-analysis"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Analyze product images using Rekognition"
  }
}

# Package Lambda function
data "archive_file" "image_analysis_zip" {
  type        = "zip"
  source_file = "./../lambda/image_analysis/handler.py"
  output_path = "modules/image_analysis/image_analysis.zip"
}

# IAM role for the Lambda function
resource "aws_iam_role" "image_analysis_role" {
  name = "${var.project_name}-${var.environment}-image-analysis-role"

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

  tags = {
    Name        = "${var.project_name}-${var.environment}-image-analysis-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for Rekognition access
resource "aws_iam_policy" "image_analysis_rekognition_policy" {
  name        = "${var.project_name}-${var.environment}-image-analysis-rekognition-policy"
  description = "Policy for image analysis Lambda to access Rekognition"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectLabels",
          "rekognition:DetectText",
          "rekognition:DetectFaces"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for DynamoDB access
resource "aws_iam_policy" "image_analysis_dynamodb_policy" {
  name        = "${var.project_name}-${var.environment}-image-analysis-dynamodb-policy"
  description = "Policy for image analysis Lambda to access DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.image_analysis.arn,
          "${aws_dynamodb_table.image_analysis.arn}/index/*"
        ]
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for S3 access
resource "aws_iam_policy" "image_analysis_s3_policy" {
  name        = "${var.project_name}-${var.environment}-image-analysis-s3-policy"
  description = "Policy for image analysis Lambda to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject"
        ]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}/*"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach policies to the role
resource "aws_iam_role_policy_attachment" "image_analysis_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.image_analysis_role.name
}

resource "aws_iam_role_policy_attachment" "image_analysis_rekognition_policy" {
  policy_arn = aws_iam_policy.image_analysis_rekognition_policy.arn
  role       = aws_iam_role.image_analysis_role.name
}

resource "aws_iam_role_policy_attachment" "image_analysis_dynamodb_policy" {
  policy_arn = aws_iam_policy.image_analysis_dynamodb_policy.arn
  role       = aws_iam_role.image_analysis_role.name
}

resource "aws_iam_role_policy_attachment" "image_analysis_s3_policy" {
  policy_arn = aws_iam_policy.image_analysis_s3_policy.arn
  role       = aws_iam_role.image_analysis_role.name
}

# Lambda permission for Bedrock agent to invoke the function
resource "aws_lambda_permission" "bedrock_invoke_image_analysis" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_analysis.function_name
  principal     = "bedrock.amazonaws.com"
}