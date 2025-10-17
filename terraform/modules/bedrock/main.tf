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

# IAM policy for Bedrock agent to access knowledge bases
resource "aws_iam_policy" "bedrock_agent_kb_policy" {
  count       = var.cultural_intelligence_kb_id != "" ? 1 : 0
  name        = "${var.project_name}-${var.environment}-bedrock-agent-kb-policy"
  description = "Policy for Bedrock agent to access knowledge bases"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}:*:knowledge-base/${var.cultural_intelligence_kb_id}"
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

resource "aws_iam_role_policy_attachment" "bedrock_agent_kb_policy" {
  count      = var.cultural_intelligence_kb_id != "" ? 1 : 0
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_kb_policy[0].arn
}

# Supervisor Bedrock Agent
resource "aws_bedrockagent_agent" "supervisor" {
  agent_name                  = "${var.project_name}-${var.environment}-supervisor"
  agent_resource_role_arn     = aws_iam_role.bedrock_agent_role.arn
  description                 = "AI supervisor agent for orchestrating multi-tier marketing campaign generation"
  foundation_model           = var.bedrock_model_id
  idle_session_ttl_in_seconds = 3600

  instruction = <<-EOT
You are an AI Marketing Campaign Supervisor responsible for orchestrating comprehensive marketing campaigns using specialized action groups and agents.

## Available Resources:
### Action Groups:
1. **image-analysis**: Analyzes product images using Amazon Rekognition - call with /analyze-product-image endpoint
2. **data-enrichment**: Enriches campaign data using YouTube API - call with /enrich-campaign-data endpoint
3. **cultural-intelligence**: Provides cross-cultural adaptation and market intelligence - call with /cultural-insights endpoint

${var.cultural_intelligence_kb_id != "" ? "### Knowledge Base:\n- **Cultural Intelligence Knowledge Base** (ID: ${var.cultural_intelligence_kb_id}): Contains cross-cultural guidelines, market intelligence, and cultural adaptation insights for global markets. You can query this knowledge base directly for cultural insights and market-specific information." : ""}

## Enhanced Campaign Generation Workflow:

### STEP 1: Image Analysis (when s3_info provided)
Call the image-analysis action group with:
```json
{
  "product_info": {
    "name": "Product Name",
    "description": "Product Description", 
    "category": "Product Category"
  },
  "s3_info": {
    "bucket": "bucket-name",
    "key": "path/to/image.jpg"
  }
}
```

### STEP 2: Data Enrichment
After image analysis, build a search query from the results and call data-enrichment:
```json
{
  "search_query": "constructed search query from image analysis results",
  "max_results": 10,
  "content_type": "videos"
}
```

### STEP 3: Cultural Intelligence (when targeting global markets)
After data enrichment, get cultural adaptation insights for target markets:
```json
{
  "target_markets": ["China", "Japan", "Germany"],
  "campaign_type": "social_media",
  "product_category": "extracted from image analysis"
}
```

### STEP 4: Campaign Generation
Use image analysis, YouTube data enrichment, AND cultural intelligence to create:
- Culturally-adapted campaign strategy based on visual elements, market trends, and cultural insights
- Platform-specific content informed by successful YouTube content and cultural preferences
- Trending keywords and hashtags adapted for each target market
- Content themes that resonate with target audiences while respecting cultural sensitivities
- Market-specific adaptations based on cultural intelligence insights

## Search Query Construction:
From image analysis results, construct search queries that include:
- Primary product keywords (from detected labels)
- Product category + "review" or "unboxing" or "demo"  
- High-confidence visual elements + target audience interests
- Example: "wireless headphones review 2024 noise cancelling" or "smartphone camera test photography"

## Key Principles:
- ALWAYS call image-analysis and data-enrichment in sequence when s3_info is provided
- When targeting multiple markets, ALSO call cultural-intelligence for cross-cultural adaptation
- Use image analysis to inform the search query for data enrichment
- Combine visual insights, market trend data, AND cultural intelligence for globally-optimized campaigns
- Provide structured JSON output with clear campaign recommendations
- Include platform-specific adaptations (Instagram, TikTok, Facebook, YouTube, Twitter) tailored for each market
- Ground recommendations in visual analysis, market data, AND cultural insights

## Output Format:
Always structure your final response as JSON with these sections:
- campaign_strategy: Overall strategy incorporating visual, trend, and cultural insights
- platform_content: Specific content for each platform with trend-informed and culturally-adapted elements
- visual_insights: Key findings from image analysis
- market_trends: Trending topics and keywords from YouTube data
- cultural_adaptations: Market-specific cultural considerations and adaptations
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

# Knowledge Base Association for Cultural Intelligence
resource "aws_bedrockagent_agent_knowledge_base_association" "cultural_intelligence_kb" {
  count                = var.cultural_intelligence_kb_id != "" ? 1 : 0
  agent_id             = aws_bedrockagent_agent.supervisor.agent_id
  agent_version        = "DRAFT"
  description          = "Cultural Intelligence Knowledge Base for cross-cultural campaign adaptation"
  knowledge_base_id    = var.cultural_intelligence_kb_id
  knowledge_base_state = "ENABLED"

  depends_on = [aws_bedrockagent_agent.supervisor]
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

  # Data enrichment OpenAPI schema
  data_enrichment_openapi_schema = jsonencode({
    openapi = "3.0.0"
    info = {
      title       = "Data Enrichment Action Group"
      version     = "1.0.0"
      description = "Action group for enriching marketing campaigns with YouTube data and trends"
    }
    paths = {
      "/enrich-campaign-data" = {
        post = {
          summary     = "Enrich campaign data with YouTube insights"
          description = "Takes a search query and enriches marketing campaign data by searching YouTube for relevant content, analyzing trends, and providing actionable insights"
          operationId = "enrich_campaign_data"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type     = "object"
                  required = ["search_query"]
                  properties = {
                    search_query = {
                      type        = "string"
                      description = "The search query to use for finding relevant YouTube content. Should be based on product name, category, and target audience"
                      example     = "wireless headphones review 2024 noise cancelling"
                      minLength   = 3
                      maxLength   = 200
                    }
                    max_results = {
                      type        = "integer"
                      description = "Maximum number of YouTube search results to retrieve and analyze"
                      example     = 15
                      minimum     = 5
                      maximum     = 50
                      default     = 10
                    }
                    content_type = {
                      type        = "string"
                      description = "Type of YouTube content to search for"
                      enum        = ["all", "videos", "channels", "playlists"]
                      example     = "videos"
                      default     = "all"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Successfully enriched campaign data with YouTube insights"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type        = "boolean"
                        description = "Indicates if the enrichment was successful"
                        example     = true
                      }
                      enrichment_id = {
                        type        = "string"
                        description = "Unique identifier for this enrichment operation"
                        example     = "enrich_12345_10"
                      }
                      results_count = {
                        type        = "integer"
                        description = "Number of YouTube results found and analyzed"
                        example     = 15
                      }
                      insights = {
                        type        = "object"
                        description = "Actionable insights generated from the enrichment data"
                        properties = {
                          content_opportunities = {
                            type = "array"
                            description = "Content creation opportunities identified"
                          }
                          trending_topics = {
                            type = "array"
                            description = "Currently trending topics in the space"
                          }
                          audience_preferences = {
                            type = "array"
                            description = "Audience preferences identified from the data"
                          }
                          competitive_landscape = {
                            type = "array"
                            description = "Analysis of the competitive landscape"
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            "400" = {
              description = "Bad request - invalid or missing parameters"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type    = "boolean"
                        example = false
                      }
                      error = {
                        type        = "string"
                        description = "Error message describing what went wrong"
                        example     = "search_query parameter is required"
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

  # Cultural Intelligence OpenAPI schema
  cultural_intelligence_openapi_schema = jsonencode({
    openapi = "3.0.0"
    info = {
      title       = "Cultural Intelligence API"
      version     = "1.0.0"
      description = "API for cross-cultural adaptation and market intelligence insights"
    }
    paths = {
      "/cultural-insights" = {
        post = {
          summary     = "Get cultural adaptation insights"
          description = "Retrieve cultural guidelines and adaptation recommendations for target markets"
          operationId = "get_cultural_insights"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type     = "object"
                  required = ["target_markets"]
                  properties = {
                    target_markets = {
                      type        = "array"
                      items       = { type = "string" }
                      description = "List of target markets for cultural adaptation"
                      example     = ["China", "Japan"]
                    }
                    campaign_type = {
                      type        = "string"
                      description = "Type of marketing campaign"
                      example     = "social_media"
                    }
                    product_category = {
                      type        = "string"
                      description = "Product category for context-specific insights"
                      example     = "fashion"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Cultural insights retrieved successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                        example = true
                      }
                      data = {
                        type = "object"
                        properties = {
                          insights_id = { type = "string" }
                          target_markets = {
                            type = "array"
                            items = { type = "string" }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            "400" = {
              description = "Bad request"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = { type = "boolean" }
                      error = { type = "string" }
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

# Image Analysis Action Group
resource "aws_bedrockagent_agent_action_group" "image_analysis" {
  count                       = var.image_analysis_lambda_arn != "" ? 1 : 0
  action_group_name          = "image-analysis"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Action group for analyzing product images using Amazon Rekognition"
  
  action_group_executor {
    lambda = var.image_analysis_lambda_arn
  }

  api_schema {
    payload = local.image_analysis_openapi_schema
  }

  prepare_agent = true

  depends_on = [aws_bedrockagent_agent.supervisor]
}

# Data Enrichment Action Group
resource "aws_bedrockagent_agent_action_group" "data_enrichment" {
  count                       = var.data_enrichment_lambda_arn != "" ? 1 : 0
  action_group_name          = "data-enrichment"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Action group for enriching marketing campaigns with YouTube data and trends"
  
  action_group_executor {
    lambda = var.data_enrichment_lambda_arn
  }

  api_schema {
    payload = local.data_enrichment_openapi_schema
  }

  prepare_agent = true

  depends_on = [aws_bedrockagent_agent.supervisor]
}

# Cultural Intelligence Action Group
resource "aws_bedrockagent_agent_action_group" "cultural_intelligence" {
  count                       = var.cultural_intelligence_lambda_arn != "" ? 1 : 0
  action_group_name          = "cultural-intelligence"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Action group for cross-cultural adaptation and market intelligence insights"
  
  action_group_executor {
    lambda = var.cultural_intelligence_lambda_arn
  }

  api_schema {
    payload = local.cultural_intelligence_openapi_schema
  }

  prepare_agent = true

  depends_on = [aws_bedrockagent_agent.supervisor]
}

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