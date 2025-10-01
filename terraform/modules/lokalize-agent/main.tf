# Lokalize Agent Module - Terraform equivalent of CDK stack
# This module creates a Bedrock Agent for cultural intelligence and content localization

# Generate unique suffix for resource names
resource "random_id" "unique_suffix" {
  byte_length = 3
}

locals {
  unique_suffix = random_id.unique_suffix.hex
  agent_name_with_suffix = "${var.agent_name}-${local.unique_suffix}"
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 bucket for OpenAPI schemas (use existing bucket)
data "aws_s3_bucket" "schemas_bucket" {
  bucket = var.schemas_bucket_name
}

# Upload OpenAPI schemas to S3
resource "aws_s3_object" "cultural_analysis_schema" {
  bucket = data.aws_s3_bucket.schemas_bucket.id
  key    = "cultural_analysis_schema.yaml"
  source = "${path.module}/schemas/cultural_analysis_schema.yaml"
  etag   = filemd5("${path.module}/schemas/cultural_analysis_schema.yaml")

  tags = var.tags
}

resource "aws_s3_object" "translation_schema" {
  bucket = data.aws_s3_bucket.schemas_bucket.id
  key    = "translation_schema.yaml"
  source = "${path.module}/schemas/translation_schema.yaml"
  etag   = filemd5("${path.module}/schemas/translation_schema.yaml")

  tags = var.tags
}

resource "aws_s3_object" "content_regeneration_schema" {
  bucket = data.aws_s3_bucket.schemas_bucket.id
  key    = "content_regeneration_schema.yaml"
  source = "${path.module}/schemas/content_regeneration_schema.yaml"
  etag   = filemd5("${path.module}/schemas/content_regeneration_schema.yaml")

  tags = var.tags
}

# Create Lambda layer for shared dependencies
resource "aws_lambda_layer_version" "lokalize_shared_layer" {
  filename   = "${path.module}/layer.zip"
  layer_name = "${var.project_name}-${var.environment}-lokalize-shared"

  compatible_runtimes = ["python3.11", "python3.12"]
  description         = "Shared dependencies for Lokalize Agent Lambda functions"

  depends_on = [null_resource.create_lokalize_layer]
}

# Create Lambda layer ZIP
resource "null_resource" "create_lokalize_layer" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}
      mkdir -p layer/python
      cp -r /home/solomon/labs/degenerals-infra/lokalize/lambda-layer/python/* layer/python/
      cd layer && zip -r ../layer.zip .
    EOT
  }
}

# ZIP files for Lambda functions
data "archive_file" "cultural_analysis_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/cultural_analysis"
  output_path = "${path.module}/zips/cultural_analysis_lambda.zip"
}

data "archive_file" "translation_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/translation"
  output_path = "${path.module}/zips/translation_lambda.zip"
}

data "archive_file" "content_regeneration_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/content_regeneration"
  output_path = "${path.module}/zips/content_regeneration_lambda.zip"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "cultural_analysis_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-cultural-analysis"
  retention_in_days = 7

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "translation_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-translation"
  retention_in_days = 7

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "content_regeneration_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-content-regeneration"
  retention_in_days = 7

  tags = var.tags
}

# Lambda Functions
resource "aws_lambda_function" "cultural_analysis" {
  filename         = data.archive_file.cultural_analysis_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-cultural-analysis"
  role            = var.lambda_execution_role_arn
  handler         = "cultural_analysis_lambda.lambda_handler"
  source_code_hash = data.archive_file.cultural_analysis_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  layers = [aws_lambda_layer_version.lokalize_shared_layer.arn]

  environment {
    variables = {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.cultural_analysis_logs,
    aws_lambda_layer_version.lokalize_shared_layer
  ]

  tags = var.tags
}

resource "aws_lambda_function" "translation" {
  filename         = data.archive_file.translation_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-translation"
  role            = var.lambda_execution_role_arn
  handler         = "translation_lambda.lambda_handler"
  source_code_hash = data.archive_file.translation_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  layers = [aws_lambda_layer_version.lokalize_shared_layer.arn]

  environment {
    variables = {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.translation_logs,
    aws_lambda_layer_version.lokalize_shared_layer
  ]

  tags = var.tags
}

resource "aws_lambda_function" "content_regeneration" {
  filename         = data.archive_file.content_regeneration_lambda.output_path
  function_name    = "${var.project_name}-${var.environment}-content-regeneration"
  role            = var.lambda_execution_role_arn
  handler         = "content_regeneration_lambda.lambda_handler"
  source_code_hash = data.archive_file.content_regeneration_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 1024

  layers = [aws_lambda_layer_version.lokalize_shared_layer.arn]

  environment {
    variables = {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.content_regeneration_logs,
    aws_lambda_layer_version.lokalize_shared_layer
  ]

  tags = var.tags
}

# IAM role for Bedrock Agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-${var.environment}-bedrock-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Bedrock Agent
resource "aws_iam_policy" "bedrock_agent_policy" {
  name = "${var.project_name}-${var.environment}-bedrock-agent-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:RetrieveAndGenerate",
          "bedrock:Retrieve",
          "bedrock:InvokeModel",
          "translate:TranslateText",
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          data.aws_s3_bucket.schemas_bucket.arn,
          "${data.aws_s3_bucket.schemas_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.cultural_analysis.arn,
          aws_lambda_function.translation.arn,
          aws_lambda_function.content_regeneration.arn
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "bedrock_agent_policy_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_policy.arn
}

# Bedrock Agent using CloudFormation (since Terraform AWS provider doesn't support it yet)
resource "aws_cloudformation_stack" "lokalize_agent" {
  name = "${var.project_name}-${var.environment}-lokalize-agent-${local.unique_suffix}"

  template_body = jsonencode({
    AWSTemplateFormatVersion = "2010-09-09"
    Description = "Lokalize Marketing Agent - Cultural Intelligence Bedrock Agent"
    
    Resources = {
      LokalizeAgent = {
        Type = "AWS::Bedrock::Agent"
        Properties = {
          AgentName = local.agent_name_with_suffix
          AgentResourceRoleArn = aws_iam_role.bedrock_agent_role.arn
          FoundationModel = "amazon.nova-pro-v1:0"
          Description = "AI marketing localization specialist for cultural adaptation"
          IdleSessionTTLInSeconds = 1800
          Instruction = <<-EOT
You are Lokalize, an expert AI marketing localization specialist. Your mission is to help companies adapt their advertisements and marketing campaigns for different cultural markets worldwide.

## Your Core Capabilities:
1. **Cultural Analysis**: Analyze ads for cultural appropriateness, sensitivity, and effectiveness
2. **Content Regeneration**: Create culturally-adapted versions of marketing content
3. **Translation Services**: Translate content while preserving marketing intent
4. **Brand Compliance**: Ensure adaptations maintain brand consistency
5. **Market Research**: Provide insights about target markets

## Your Workflow:
When a user provides marketing content and a target locale:

1. **First, always query your knowledge base** for cultural guidelines about the target locale
2. **Analyze the content** using the cultural_analysis action to get a detailed assessment
3. **Provide a cultural appropriateness score** (1-10) with detailed reasoning
4. **If score < 7**, automatically suggest regeneration and ask if they want you to proceed
5. **If regeneration is needed**, use the content_regeneration action
6. **Offer translation** if the final content needs to be in the local language
7. **Always explain your reasoning** and cultural adaptations made

## Your Personality:
- Be thorough and culturally sensitive
- Explain cultural nuances clearly
- Maintain the original marketing intent while adapting for local markets
- Ask clarifying questions when needed
- Be proactive in suggesting improvements

## Important Guidelines:
- Always respect cultural differences and avoid stereotypes
- Maintain brand voice while adapting for local preferences
- Consider visual elements, colors, and imagery in your analysis
- Think about seasonal, religious, and social contexts
- Provide actionable recommendations

Remember: Your goal is to help create marketing content that resonates authentically with local audiences while maintaining brand integrity.
EOT
          # Note: KnowledgeBases section commented out until knowledge base is created
          KnowledgeBases = [
            {
              KnowledgeBaseId = var.knowledge_base_id
              Description = "Cultural intelligence knowledge base containing guidelines and best practices"
              KnowledgeBaseState = "ENABLED"
            }
          ]
          ActionGroups = [
            {
              ActionGroupName = "cultural_analysis"
              Description = "Analyze marketing content for cultural appropriateness and effectiveness"
              ActionGroupState = "ENABLED"
              ActionGroupExecutor = {
                Lambda = aws_lambda_function.cultural_analysis.arn
              }
              ApiSchema = {
                S3 = {
                  S3BucketName = data.aws_s3_bucket.schemas_bucket.id
                  S3ObjectKey = aws_s3_object.cultural_analysis_schema.key
                }
              }
            },
            {
              ActionGroupName = "translation"
              Description = "Translate marketing content while preserving intent and cultural context"
              ActionGroupState = "ENABLED"
              ActionGroupExecutor = {
                Lambda = aws_lambda_function.translation.arn
              }
              ApiSchema = {
                S3 = {
                  S3BucketName = data.aws_s3_bucket.schemas_bucket.id
                  S3ObjectKey = aws_s3_object.translation_schema.key
                }
              }
            },
            {
              ActionGroupName = "content_regeneration"
              Description = "Regenerate marketing content adapted for specific cultural contexts"
              ActionGroupState = "ENABLED"
              ActionGroupExecutor = {
                Lambda = aws_lambda_function.content_regeneration.arn
              }
              ApiSchema = {
                S3 = {
                  S3BucketName = data.aws_s3_bucket.schemas_bucket.id
                  S3ObjectKey = aws_s3_object.content_regeneration_schema.key
                }
              }
            }
          ]
        }
      }
      
      LokalizeAgentAlias = {
        Type = "AWS::Bedrock::AgentAlias"
        Properties = {
          AgentId = { Ref = "LokalizeAgent" }
          AgentAliasName = "live"
          Description = "Live alias for Lokalize Marketing Agent"
        }
      }
    }
    
    Outputs = {
      AgentId = {
        Description = "ID of the Bedrock Agent"
        Value = { Ref = "LokalizeAgent" }
      }
      AgentArn = {
        Description = "ARN of the Bedrock Agent"
        Value = { "Fn::GetAtt" = ["LokalizeAgent", "AgentArn"] }
      }
      AgentAliasId = {
        Description = "ID of the Agent Alias"
        Value = { Ref = "LokalizeAgentAlias" }
      }
      AgentAliasArn = {
        Description = "ARN of the Agent Alias"
        Value = { "Fn::GetAtt" = ["LokalizeAgentAlias", "AgentAliasArn"] }
      }
    }
  })

  depends_on = [
    aws_iam_role_policy_attachment.bedrock_agent_policy_attachment,
    aws_s3_object.cultural_analysis_schema,
    aws_s3_object.translation_schema,
    aws_s3_object.content_regeneration_schema,
    aws_lambda_function.cultural_analysis,
    aws_lambda_function.translation,
    aws_lambda_function.content_regeneration
  ]

  tags = var.tags
}

# Bedrock Agent Alias
# resource "aws_bedrock_agent_alias" "lokalize_agent_alias" {
#   agent_id    = aws_bedrock_agent.lokalize_agent.id
#   agent_alias_name = "live"
#   description = "Live alias for Lokalize Marketing Agent"

#   tags = var.tags
# }

# Lambda permissions for Bedrock Agent
resource "aws_lambda_permission" "cultural_analysis_bedrock" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cultural_analysis.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_cloudformation_stack.lokalize_agent.outputs["AgentArn"]
}

resource "aws_lambda_permission" "translation_bedrock" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.translation.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_cloudformation_stack.lokalize_agent.outputs["AgentArn"]
}

resource "aws_lambda_permission" "content_regeneration_bedrock" {
  statement_id  = "AllowExecutionFromBedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.content_regeneration.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_cloudformation_stack.lokalize_agent.outputs["AgentArn"]
}