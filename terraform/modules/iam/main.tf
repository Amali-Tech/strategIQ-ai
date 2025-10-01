# IAM Module
# This module manages IAM resources for the AWS AI Hackathon project

# Random suffix for IAM resources to avoid conflicts
resource "random_string" "iam_suffix" {
  length  = 6
  special = false
  upper   = false
}

# Lambda Execution Role for Image Analysis Functions
resource "aws_iam_role" "lambda_image_analysis_role" {
  name = "${var.project_name}-${var.environment}-lambda-image-analysis-role-${random_string.iam_suffix.result}"

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

# Lambda Execution Role for Campaign Generation Functions
resource "aws_iam_role" "lambda_campaign_role" {
  name = "${var.project_name}-${var.environment}-lambda-campaign-role-${random_string.iam_suffix.result}"

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

# Lambda Execution Role for API Functions (CRUD, Presigned URL)
resource "aws_iam_role" "lambda_api_role" {
  name = "${var.project_name}-${var.environment}-lambda-api-role-${random_string.iam_suffix.result}"

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

# Lambda Execution Role for Sentiment Analysis Functions
resource "aws_iam_role" "lambda_sentiment_role" {
  name = "${var.project_name}-${var.environment}-lambda-sentiment-role-${random_string.iam_suffix.result}"

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

# Lambda Execution Role for Lokalize Functions
resource "aws_iam_role" "lambda_lokalize_role" {
  name = "${var.project_name}-${var.environment}-lambda-lokalize-role-${random_string.iam_suffix.result}"

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

# EventBridge Role for Pipes
resource "aws_iam_role" "eventbridge_pipes_role" {
  name = "${var.project_name}-${var.environment}-eventbridge-pipes-role-${random_string.iam_suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "pipes.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Policy for S3 Access (Image upload/download)
resource "aws_iam_policy" "s3_access_policy" {
  name = "${var.project_name}-${var.environment}-s3-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectAcl",
          "s3:GetObjectTagging",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })

  tags = var.tags
}

# Policy for DynamoDB Access
resource "aws_iam_policy" "dynamodb_access_policy" {
  name = "${var.project_name}-${var.environment}-dynamodb-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:DescribeTable"
        ]
        Resource = var.dynamodb_table_arns
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams"
        ]
        Resource = var.dynamodb_stream_arns
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:*",
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Policy for Rekognition Access
resource "aws_iam_policy" "rekognition_access_policy" {
  name = "${var.project_name}-${var.environment}-rekognition-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectLabels",
          "rekognition:DetectText",
          "rekognition:DetectModerationLabels",
          "rekognition:RecognizeCelebrities"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = var.tags
}

# Policy for Bedrock Access
resource "aws_iam_policy" "bedrock_access_policy" {
  name = "${var.project_name}-${var.environment}-bedrock-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-*",
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-v2*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeAgent",
          "bedrock:RetrieveAndGenerate",
          "bedrock:Retrieve"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Policy for Comprehend Access
resource "aws_iam_policy" "comprehend_access_policy" {
  name = "${var.project_name}-${var.environment}-comprehend-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectSentiment",
          "comprehend:DetectEntities",
          "comprehend:DetectKeyPhrases",
          "comprehend:DetectLanguage"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Policy for SQS Access
resource "aws_iam_policy" "sqs_access_policy" {
  name = "${var.project_name}-${var.environment}-sqs-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = var.sqs_queue_arns
      }
    ]
  })

  tags = var.tags
}

# Policy for EventBridge Pipes
resource "aws_iam_policy" "eventbridge_pipes_policy" {
  name = "${var.project_name}-${var.environment}-eventbridge-pipes-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams"
        ]
        Resource = var.dynamodb_stream_arns
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = var.sqs_queue_arns
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:*:*:function:${var.project_name}-${var.environment}-*"
      }
    ]
  })

  tags = var.tags
}

# Policy for Translate Access
resource "aws_iam_policy" "translate_access_policy" {
  name = "${var.project_name}-${var.environment}-translate-access-policy-${random_string.iam_suffix.result}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "translate:TranslateText",
          "translate:GetTerminology",
          "translate:ListTerminologies"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Attach policies to Image Analysis Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_image_analysis_basic" {
  role       = aws_iam_role.lambda_image_analysis_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_image_analysis_s3" {
  role       = aws_iam_role.lambda_image_analysis_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_image_analysis_dynamodb" {
  role       = aws_iam_role.lambda_image_analysis_role.name
  policy_arn = aws_iam_policy.dynamodb_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_image_analysis_rekognition" {
  role       = aws_iam_role.lambda_image_analysis_role.name
  policy_arn = aws_iam_policy.rekognition_access_policy.arn
}

# Attach policies to Campaign Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_campaign_basic" {
  role       = aws_iam_role.lambda_campaign_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_campaign_dynamodb" {
  role       = aws_iam_role.lambda_campaign_role.name
  policy_arn = aws_iam_policy.dynamodb_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_campaign_bedrock" {
  role       = aws_iam_role.lambda_campaign_role.name
  policy_arn = aws_iam_policy.bedrock_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_campaign_comprehend" {
  role       = aws_iam_role.lambda_campaign_role.name
  policy_arn = aws_iam_policy.comprehend_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_campaign_sqs" {
  role       = aws_iam_role.lambda_campaign_role.name
  policy_arn = aws_iam_policy.sqs_access_policy.arn
}

# Attach policies to API Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_api_basic" {
  role       = aws_iam_role.lambda_api_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_api_s3" {
  role       = aws_iam_role.lambda_api_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_api_dynamodb" {
  role       = aws_iam_role.lambda_api_role.name
  policy_arn = aws_iam_policy.dynamodb_access_policy.arn
}

# Attach policies to EventBridge Pipes Role
resource "aws_iam_role_policy_attachment" "eventbridge_pipes_policy_attachment" {
  role       = aws_iam_role.eventbridge_pipes_role.name
  policy_arn = aws_iam_policy.eventbridge_pipes_policy.arn
}

# Attach policies to Sentiment Analysis Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_sentiment_basic" {
  role       = aws_iam_role.lambda_sentiment_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_sentiment_comprehend" {
  role       = aws_iam_role.lambda_sentiment_role.name
  policy_arn = aws_iam_policy.comprehend_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_sentiment_dynamodb" {
  role       = aws_iam_role.lambda_sentiment_role.name
  policy_arn = aws_iam_policy.dynamodb_access_policy.arn
}

# Attach policies to Lokalize Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_lokalize_basic" {
  role       = aws_iam_role.lambda_lokalize_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_lokalize_bedrock" {
  role       = aws_iam_role.lambda_lokalize_role.name
  policy_arn = aws_iam_policy.bedrock_access_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_lokalize_translate" {
  role       = aws_iam_role.lambda_lokalize_role.name
  policy_arn = aws_iam_policy.translate_access_policy.arn
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}

