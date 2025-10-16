# Bedrock Module
# This module manages Bedrock agent resources for AI campaign orchestration

# IAM role for Bedrock agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-${var.environment}-bedrock-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Bedrock agent execution role"
  }
}

# IAM policy for Bedrock agent to invoke Lambda functions
resource "aws_iam_policy" "bedrock_agent_lambda_policy" {
  name        = "${var.project_name}-${var.environment}-bedrock-agent-lambda-policy"
  description = "Policy for Bedrock agent to invoke Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = compact([
          var.image_analysis_lambda_arn != "" ? var.image_analysis_lambda_arn : null,
          var.campaign_generation_lambda_arn != "" ? var.campaign_generation_lambda_arn : null,
          var.voice_of_market_lambda_arn != "" ? var.voice_of_market_lambda_arn : null,
          var.lokalize_lambda_arn != "" ? var.lokalize_lambda_arn : null,
          # Allow all Lambda functions in the account for now (will be restricted later)
          "arn:aws:lambda:${var.aws_region}:*:function:${var.project_name}-${var.environment}-*"
        ])
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for Bedrock agent to use foundation models and inference profiles
resource "aws_iam_policy" "bedrock_agent_model_policy" {
  name        = "${var.project_name}-${var.environment}-bedrock-agent-model-policy"
  description = "Policy for Bedrock agent to use foundation models and inference profiles"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:GetInferenceProfile",
          "bedrock:ListInferenceProfiles"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}:584102815888:inference-profile/eu.amazon.nova-pro-v1:0"
        ]
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach policies to the Bedrock agent role
resource "aws_iam_role_policy_attachment" "bedrock_agent_lambda_policy" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "bedrock_agent_model_policy" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_model_policy.arn
}

# Supervisor Bedrock Agent
resource "aws_bedrockagent_agent" "supervisor" {
  agent_name                  = "${var.project_name}-${var.environment}-supervisor"
  agent_resource_role_arn     = aws_iam_role.bedrock_agent_role.arn
  description                 = "AI supervisor agent for orchestrating multi-tier marketing campaign generation"
  foundation_model           = var.bedrock_model_id
  idle_session_ttl_in_seconds = 3600

  instruction = <<-EOT
You are an AI Marketing Campaign Supervisor responsible for orchestrating comprehensive marketing campaigns using specialized AI agents.

## Your Role:
You coordinate between three specialist agents to create culturally-aware, data-driven marketing campaigns:
1. **campaign-generation**: Creates campaigns, analyzes images, enriches product data
2. **voice-of-the-market**: Provides market analysis, competitive intelligence, sentiment analysis  
3. **lokalize**: Handles cultural adaptation and localization for target markets

## Core Workflows:

### TIER 1 - Basic Campaign Generation
For standard campaign requests:
1. InvokeAgent: campaign-generation - Use image-analysis and data-enrichment tools to analyze the product
2. InvokeAgent: campaign-generation - Use campaign-ideas tool to generate platform-specific content
3. Synthesize results into a cohesive campaign strategy

### TIER 2 - Market-Optimized Campaigns  
For campaigns requiring market intelligence:
1. InvokeAgent: voice-of-the-market - Analyze market conditions and competitive landscape
2. InvokeAgent: campaign-generation - Generate campaigns incorporating market insights
3. InvokeAgent: lokalize - Adapt content for cultural appropriateness
4. Combine all insights for optimized campaign strategy

### TIER 3 - Global Viral Campaigns
For comprehensive global campaigns:
1. InvokeAgent: voice-of-the-market - Deep market analysis across all target regions
2. InvokeAgent: campaign-generation - Create foundational campaign concepts
3. InvokeAgent: lokalize - Comprehensive cultural adaptation for each market
4. InvokeAgent: voice-of-the-market - Validate cultural adaptations against market sentiment
5. Orchestrate final global campaign strategy

## Key Principles:
- Always provide structured JSON output with clear campaign recommendations
- Include platform-specific adaptations (Instagram, TikTok, Facebook, YouTube, Twitter)
- Ensure cultural sensitivity through lokalize agent validation
- Ground all recommendations in market data when available
- Provide actionable next steps and success metrics

## Output Format:
Always structure your final response as JSON with these sections:
- campaign_strategy: Overall strategy and positioning
- platform_content: Specific content for each platform
- cultural_adaptations: Market-specific modifications
- success_metrics: KPIs and measurement recommendations
- next_steps: Implementation guidance
EOT

  prepare_agent = true

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "AI campaign orchestration supervisor"
  }
}

# OpenAPI schema for image analysis action group
locals {
  image_analysis_openapi_schema = jsonencode({
    openapi = "3.0.0"
    info = {
      title       = "Image Analysis Action Group"
      version     = "1.0.0"
      description = "Action group for analyzing product images using Amazon Rekognition"
    }
    paths = {
      "/analyze-product-image" = {
        post = {
          summary     = "Analyze product image using Rekognition"
          description = "Analyzes a product image from S3 using Amazon Rekognition to detect labels, then stores structured analysis data in DynamoDB"
          operationId = "analyze_product_image"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type     = "object"
                  required = ["product_info", "s3_info"]
                  properties = {
                    product_info = {
                      type        = "object"
                      description = "Information about the product being analyzed"
                      required    = ["name"]
                      properties = {
                        name = {
                          type        = "string"
                          description = "Product name"
                          example     = "EcoSmart Water Bottle"
                        }
                        description = {
                          type        = "string"
                          description = "Product description"
                          example     = "Smart water bottle with temperature control"
                        }
                        category = {
                          type        = "string"
                          description = "Product category"
                          example     = "Health & Wellness"
                        }
                      }
                    }
                    s3_info = {
                      type        = "object"
                      description = "S3 location of the product image"
                      required    = ["bucket", "key"]
                      properties = {
                        bucket = {
                          type        = "string"
                          description = "S3 bucket name containing the image"
                          example     = "degenerals-mi-dev-images"
                        }
                        key = {
                          type        = "string"
                          description = "S3 object key (path) to the image file"
                          example     = "uploads/product-images/water-bottle.jpg"
                        }
                      }
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Image analysis completed successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type    = "boolean"
                        example = true
                      }
                      data = {
                        type = "object"
                        properties = {
                          analysis_id = {
                            type        = "string"
                            description = "Unique identifier for this analysis"
                          }
                          product_name = {
                            type        = "string"
                            description = "Name of the analyzed product"
                          }
                          detected_labels = {
                            type        = "array"
                            description = "Top detected labels from Rekognition"
                            items = {
                              type = "object"
                              properties = {
                                name       = { type = "string" }
                                confidence = { type = "number", format = "float" }
                                categories = { type = "array", items = { type = "string" } }
                              }
                            }
                          }
                          recommendations = {
                            type        = "object"
                            description = "Campaign recommendations based on image analysis"
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })
}

# Note: Action groups need to be created manually via AWS Console or CLI
# as aws_bedrockagent_action_group resource is not yet available in terraform
# 
# Manual steps required after terraform apply:
# 1. Go to Bedrock Console > Agents > Select supervisor agent
# 2. Add Action Group with name "image-analysis" 
# 3. Set Lambda function to: module.image_analysis.lambda_function_arn
# 4. Upload the OpenAPI schema from lambda/image_analysis/openapi_schema.json
# 5. Prepare the agent

# Create agent alias for stable endpoint
resource "aws_bedrockagent_agent_alias" "supervisor_alias" {
  agent_alias_name = "${var.environment}-alias"
  agent_id         = aws_bedrockagent_agent.supervisor.agent_id
  description      = "Stable alias for supervisor agent in ${var.environment} environment"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}