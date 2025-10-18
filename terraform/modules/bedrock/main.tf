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
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
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
          "${var.bedrock_agent_inference_profile_arn}"
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
  agent_name                  = "${var.project_name}-${var.environment}-supervisor-claude"
  agent_resource_role_arn     = aws_iam_role.bedrock_agent_role.arn
  description                 = "AI supervisor agent for orchestrating multi-tier marketing campaign generation"
  foundation_model           = var.bedrock_model_id
  idle_session_ttl_in_seconds = 3600

  instruction = <<-EOT
You are a Marketing Campaign AI Agent with access to these action groups:

1. **data-enrichment** - Call with /enrich-campaign-data endpoint
2. **image-analysis** - Call with /analyze-product-image endpoint  
3. **cultural-intelligence** - Call with /cultural-insights endpoint
4. **sentiment-analysis** - Call with /analyze-sentiment endpoint

## MANDATORY WORKFLOW:

### STEP 1: Call data-enrichment action group FIRST
You MUST call the data-enrichment action group using this exact payload:
```json
{
  "search_query": "[product name] [product category] review tutorial",
  "max_results": 15,
  "content_type": "videos"
}
```

### STEP 2: Extract video IDs from response
The data-enrichment response contains a "video_data" array with "video_id" fields. Extract ALL video_id values.

### STEP 3: Return ONLY JSON conforming to this schema
Return ONLY JSON that conforms to the following schema with proper data types and validation:

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["product", "content_ideas", "campaigns", "generated_assets", "platform_content", "market_trends", "success_metrics", "analytics", "related_youtube_videos"],
  "properties": {
    "product": {
      "type": "object",
      "required": ["description", "image"],
      "properties": {
        "description": {
          "type": "string",
          "minLength": 20,
          "maxLength": 500,
          "description": "Product name and description"
        },
        "image": {
          "type": "object",
          "required": ["labels"],
          "properties": {
            "labels": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": { "type": "string", "minLength": 1 },
                  "confidence": { "type": "number", "minimum": 0, "maximum": 100 }
                }
              },
              "minItems": 0,
              "maxItems": 20
            }
          }
        }
      }
    },
    "content_ideas": {
      "type": "array",
      "minItems": 3,
      "maxItems": 10,
      "items": {
        "type": "object",
        "required": ["platform", "topic", "engagement_score", "caption", "hashtags"],
        "properties": {
          "platform": {
            "type": "string",
            "enum": ["Instagram", "TikTok", "YouTube", "LinkedIn", "Twitter", "Facebook"]
          },
          "topic": {
            "type": "string",
            "minLength": 10,
            "maxLength": 200
          },
          "engagement_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100
          },
          "caption": {
            "type": "string",
            "minLength": 20,
            "maxLength": 500
          },
          "hashtags": {
            "type": "array",
            "minItems": 3,
            "maxItems": 20,
            "items": {
              "type": "string",
              "pattern": "^#[a-zA-Z0-9_]{1,30}$"
            }
          }
        }
      }
    },
    "campaigns": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["name", "duration", "posts_per_week", "platforms", "calendar", "adaptations"],
        "properties": {
          "name": {
            "type": "string",
            "minLength": 10,
            "maxLength": 100
          },
          "duration": {
            "type": "string",
            "pattern": "^\\d+\\s+(weeks?|days?|months?)$"
          },
          "posts_per_week": {
            "type": "integer",
            "minimum": 1,
            "maximum": 14
          },
          "platforms": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
              "type": "string",
              "enum": ["Instagram", "TikTok", "YouTube", "LinkedIn", "Twitter", "Facebook", "Pinterest"]
            }
          },
          "calendar": {
            "type": "object",
            "minProperties": 2,
            "additionalProperties": {
              "type": "string",
              "minLength": 10,
              "maxLength": 200
            }
          },
          "adaptations": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
              "type": "string",
              "minLength": 20,
              "maxLength": 300
            }
          }
        }
      }
    },
    "generated_assets": {
      "type": "object",
      "required": ["image_prompts", "video_scripts", "email_templates", "blog_outlines"],
      "properties": {
        "image_prompts": {
          "type": "array",
          "minItems": 2,
          "maxItems": 10,
          "items": {
            "type": "string",
            "minLength": 20,
            "maxLength": 300
          }
        },
        "video_scripts": {
          "type": "array",
          "minItems": 2,
          "maxItems": 5,
          "items": {
            "type": "object",
            "required": ["type", "content"],
            "properties": {
              "type": {
                "type": "string",
                "enum": ["Short form video", "Long form video", "Explainer video", "Tutorial video"]
              },
              "content": {
                "type": "string",
                "minLength": 50,
                "maxLength": 2000
              }
            }
          }
        },
        "email_templates": {
          "type": "array",
          "minItems": 1,
          "maxItems": 5,
          "items": {
            "type": "object",
            "required": ["subject", "body"],
            "properties": {
              "subject": {
                "type": "string",
                "minLength": 10,
                "maxLength": 100
              },
              "body": {
                "type": "string",
                "minLength": 50,
                "maxLength": 1000
              }
            }
          }
        },
        "blog_outlines": {
          "type": "array",
          "minItems": 1,
          "maxItems": 3,
          "items": {
            "type": "object",
            "required": ["title", "points"],
            "properties": {
              "title": {
                "type": "string",
                "minLength": 10,
                "maxLength": 150
              },
              "points": {
                "type": "array",
                "minItems": 3,
                "maxItems": 10,
                "items": {
                  "type": "string",
                  "minLength": 10,
                  "maxLength": 200
                }
              }
            }
          }
        }
      }
    },
    "platform_content": {
      "type": "object",
      "required": ["instagram", "tiktok", "youtube"],
      "properties": {
        "instagram": {
          "type": "object",
          "required": ["content_themes", "recommended_formats", "sample_post", "hashtags", "posting_schedule"],
          "properties": {
            "content_themes": {
              "type": "array",
              "minItems": 1,
              "maxItems": 5,
              "items": { "type": "string" }
            },
            "recommended_formats": {
              "type": "array",
              "minItems": 1,
              "maxItems": 4,
              "items": {
                "type": "string",
                "enum": ["photo", "reel", "carousel", "story", "igtv"]
              }
            },
            "sample_post": {
              "type": "string",
              "minLength": 20,
              "maxLength": 2200
            },
            "hashtags": {
              "type": "array",
              "minItems": 5,
              "maxItems": 30,
              "items": {
                "type": "string",
                "pattern": "^#[a-zA-Z0-9_]{1,30}$"
              }
            },
            "posting_schedule": {
              "type": "string",
              "minLength": 5,
              "maxLength": 100
            }
          }
        },
        "tiktok": {
          "type": "object",
          "required": ["content_themes", "recommended_formats", "sample_post", "hashtags", "trending_sounds"],
          "properties": {
            "content_themes": {
              "type": "array",
              "minItems": 1,
              "maxItems": 5,
              "items": { "type": "string" }
            },
            "recommended_formats": {
              "type": "array",
              "minItems": 1,
              "maxItems": 4,
              "items": {
                "type": "string",
                "enum": ["short_video", "tutorial", "challenge", "duet", "stitch"]
              }
            },
            "sample_post": {
              "type": "string",
              "minLength": 20,
              "maxLength": 500
            },
            "hashtags": {
              "type": "array",
              "minItems": 5,
              "maxItems": 30,
              "items": {
                "type": "string",
                "pattern": "^#[a-zA-Z0-9_]{1,30}$"
              }
            },
            "trending_sounds": {
              "type": "array",
              "minItems": 1,
              "maxItems": 5,
              "items": { "type": "string" }
            }
          }
        },
        "youtube": {
          "type": "object",
          "required": ["content_themes", "recommended_formats", "sample_post", "video_ideas", "seo_keywords"],
          "properties": {
            "content_themes": {
              "type": "array",
              "minItems": 1,
              "maxItems": 5,
              "items": { "type": "string" }
            },
            "recommended_formats": {
              "type": "array",
              "minItems": 1,
              "maxItems": 4,
              "items": {
                "type": "string",
                "enum": ["long_form", "shorts", "live", "premiere"]
              }
            },
            "sample_post": {
              "type": "string",
              "minLength": 50,
              "maxLength": 500
            },
            "video_ideas": {
              "type": "array",
              "minItems": 2,
              "maxItems": 10,
              "items": { "type": "string" }
            },
            "seo_keywords": {
              "type": "array",
              "minItems": 5,
              "maxItems": 20,
              "items": {
                "type": "string",
                "minLength": 2,
                "maxLength": 50
              }
            }
          }
        }
      }
    },
    "market_trends": {
      "type": "object",
      "required": ["trending_keywords", "competitor_insights", "market_opportunities", "seasonal_trends"],
      "properties": {
        "trending_keywords": {
          "type": "array",
          "minItems": 3,
          "maxItems": 20,
          "items": { "type": "string" }
        },
        "competitor_insights": {
          "type": "array",
          "minItems": 2,
          "maxItems": 10,
          "items": { "type": "string" }
        },
        "market_opportunities": {
          "type": "array",
          "minItems": 2,
          "maxItems": 10,
          "items": { "type": "string" }
        },
        "seasonal_trends": {
          "type": "array",
          "minItems": 1,
          "maxItems": 8,
          "items": { "type": "string" }
        }
      }
    },
    "success_metrics": {
      "type": "object",
      "required": ["engagement_targets", "reach_goals", "conversion_metrics"],
      "properties": {
        "engagement_targets": {
          "type": "object",
          "required": ["likes", "comments", "shares"],
          "properties": {
            "likes": {
              "type": "string",
              "pattern": "^\\d+(-\\d+)?%?$"
            },
            "comments": {
              "type": "string",
              "pattern": "^\\d+(-\\d+)?%?$"
            },
            "shares": {
              "type": "string",
              "pattern": "^\\d+(-\\d+)?%?$"
            }
          }
        },
        "reach_goals": {
          "type": "object",
          "required": ["impressions", "unique_users"],
          "properties": {
            "impressions": {
              "type": "string",
              "pattern": "^\\d+[K|M]?\\+?$"
            },
            "unique_users": {
              "type": "string",
              "pattern": "^\\d+[K|M]?\\+?$"
            }
          }
        },
        "conversion_metrics": {
          "type": "object",
          "required": ["click_through_rate", "conversion_rate"],
          "properties": {
            "click_through_rate": {
              "type": "string",
              "pattern": "^\\d+(-\\d+)?%$"
            },
            "conversion_rate": {
              "type": "string",
              "pattern": "^\\d+(-\\d+)?%$"
            }
          }
        }
      }
    },
    "analytics": {
      "type": "object",
      "required": ["estimatedReach", "projectedEngagement", "conversionRate", "roi"],
      "properties": {
        "estimatedReach": {
          "type": "integer",
          "minimum": 1000,
          "maximum": 10000000
        },
        "projectedEngagement": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 100
        },
        "conversionRate": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 50
        },
        "roi": {
          "type": "number",
          "minimum": 0.5,
          "maximum": 100
        }
      }
    },
    "related_youtube_videos": {
      "type": "array",
      "minItems": 3,
      "maxItems": 50,
      "items": {
        "type": "string",
        "minLength": 5,
        "pattern": "^[a-zA-Z0-9_-]{11}$",
        "description": "YouTube video IDs from data enrichment response"
      }
    }
  }
}

## ACTION GROUP USAGE EXAMPLES:

### Call data-enrichment:
```
Action: data-enrichment
Endpoint: /enrich-campaign-data  
Payload: {"search_query": "smart fitness tracker wearables review", "max_results": 15, "content_type": "videos"}
```

### Call image-analysis (if s3_info provided):
```
Action: image-analysis
Endpoint: /analyze-product-image
Payload: {"product_info": {"name": "Product", "description": "Desc", "category": "Cat"}, "s3_info": {"bucket": "bucket", "key": "key"}}
```

CRITICAL RULES:
1. ALWAYS call data-enrichment action group first using the exact endpoint /enrich-campaign-data
2. Extract ALL video_id values from the data enrichment response
3. Put the actual video IDs in related_youtube_videos array (not placeholders)
4. Return ONLY JSON - no markdown, no explanations, no function calls in output
5. Replace [bracketed placeholders] with actual content based on product info and action group responses
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
  description          = "Cultural Intelligence Knowledge Base for adaptation"
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

  # Sentiment Analysis OpenAPI schema
  sentiment_analysis_openapi_schema = jsonencode({
    openapi = "3.0.0"
    info = {
      title       = "Sentiment Analysis API"
      version     = "1.0.0"
      description = "API for analyzing sentiment from search results and generating actionable insights"
    }
    paths = {
      "/analyze-sentiment" = {
        post = {
          summary     = "Analyze sentiment from search results"
          description = "Searches for content related to a product/brand, analyzes sentiment using AWS Comprehend, and returns aggregated results"
          operationId = "analyze_sentiment"
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
                      description = "Search query to find content for sentiment analysis (e.g., product name, brand)"
                    }
                    product_name = {
                      type        = "string"
                      description = "Optional specific product name for analysis context"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Sentiment analysis completed successfully"
            }
          }
        }
      }
      "/generate-action-items" = {
        post = {
          summary     = "Generate action items from sentiment analysis"
          description = "Uses Bedrock to generate actionable recommendations based on sentiment analysis results"
          operationId = "generate_action_items"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type = "object"
                  properties = {
                    analysis_id = {
                      type        = "string"
                      description = "ID of existing sentiment analysis to generate actions for"
                    }
                    search_query = {
                      type        = "string"
                      description = "Search query to perform fresh sentiment analysis for action generation"
                    }
                    sentiment_data = {
                      type        = "object"
                      description = "Pre-computed sentiment analysis data"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Action items generated successfully"
            }
          }
        }
      }
      "/comprehensive-sentiment-analysis" = {
        post = {
          summary     = "Comprehensive sentiment analysis with action items"
          description = "Performs complete sentiment analysis and generates action items in a single call"
          operationId = "comprehensive_sentiment_analysis"
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
                      description = "Search query to find content for sentiment analysis"
                    }
                    product_name = {
                      type        = "string"
                      description = "Optional specific product name for analysis context"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Comprehensive analysis completed successfully"
            }
          }
        }
      }
    }
  })

  # Visual Asset Generator OpenAPI schema
  visual_asset_generator_openapi_schema = jsonencode({
    openapi = "3.0.0"
    info = {
      title       = "Visual Asset Generator API"
      version     = "1.0.0"
      description = "API for generating visual assets including video scripts, social media images, thumbnails, and ad creatives"
    }
    paths = {
      "/generate-visual-assets" = {
        post = {
          summary     = "Generate visual assets for marketing campaigns"
          description = "Creates comprehensive visual assets including video scripts for multiple platforms, social media images, thumbnails, and ad creatives"
          operationId = "generate_visual_assets"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type     = "object"
                  required = ["campaign_data"]
                  properties = {
                    campaign_data = {
                      type        = "object"
                      description = "Campaign information for generating visual assets"
                      required    = ["campaign_id", "product_name"]
                      properties = {
                        campaign_id = {
                          type        = "string"
                          description = "Unique identifier for the campaign"
                        }
                        product_name = {
                          type        = "string"
                          description = "Name of the product being promoted"
                        }
                        description = {
                          type        = "string"
                          description = "Product or campaign description"
                        }
                        target_audience = {
                          type        = "string"
                          description = "Target audience for the campaign"
                        }
                        key_features = {
                          type        = "array"
                          items       = { type = "string" }
                          description = "Key product features to highlight"
                        }
                        brand_tone = {
                          type        = "string"
                          description = "Brand tone and voice"
                        }
                      }
                    }
                    asset_types = {
                      type        = "array"
                      items       = { type = "string" }
                      description = "Types of assets to generate"
                    }
                  }
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Visual assets generated successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                      }
                      campaign_id = {
                        type = "string"
                      }
                      generated_assets = {
                        type = "object"
                      }
                      total_assets = {
                        type = "integer"
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

# Image Analysis Action Group
resource "aws_bedrockagent_agent_action_group" "image_analysis" {
  action_group_name          = "image-analysis"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Analyze product images using Amazon Rekognition"
  
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
  action_group_name          = "data-enrichment"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Enrich campaigns with YouTube data and trends"
  
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
  action_group_name          = "cultural-intelligence"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Cross-cultural adaptation and market intelligence"
  
  action_group_executor {
    lambda = var.cultural_intelligence_lambda_arn
  }

  api_schema {
    payload = local.cultural_intelligence_openapi_schema
  }

  prepare_agent = true

  depends_on = [aws_bedrockagent_agent.supervisor]
}

# Sentiment Analysis Action Group
resource "aws_bedrockagent_agent_action_group" "sentiment_analysis" {
  action_group_name          = "sentiment-analysis"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Market sentiment analysis and actionable insights"
  
  action_group_executor {
    lambda = var.sentiment_analysis_lambda_arn
  }

  api_schema {
    payload = local.sentiment_analysis_openapi_schema
  }

  prepare_agent = true

  depends_on = [aws_bedrockagent_agent.supervisor]
}

# Visual Asset Generator Action Group - DISABLED for async processing
# resource "aws_bedrockagent_agent_action_group" "visual_asset_generator" {
#   count                       = var.visual_asset_generator_lambda_arn != "" ? 1 : 0
#   action_group_name          = "visual-asset-generator"
#   agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
#   agent_version              = "DRAFT"
#   description                = "Action group for generating visual assets including video scripts, social media images, thumbnails, and ad creatives"
#   
#   action_group_executor {
#     lambda = var.visual_asset_generator_lambda_arn
#   }
#
#   api_schema {
#     payload = local.visual_asset_generator_openapi_schema
#   }
#
#   prepare_agent = true
#
#   depends_on = [aws_bedrockagent_agent.supervisor]
# }

# Create agent alias for stable endpoint (only if no override is provided)
resource "aws_bedrockagent_agent_alias" "supervisor_alias" {
  count            = var.supervisor_agent_alias_id_override == "" ? 1 : 0
  agent_alias_name = "${var.environment}-alias"
  agent_id         = aws_bedrockagent_agent.supervisor.agent_id
  description      = "Stable alias for supervisor agent in ${var.environment} environment"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}