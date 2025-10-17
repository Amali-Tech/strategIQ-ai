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

NOTE: Visual asset generation happens asynchronously after campaign completion via event-driven architecture.

${var.cultural_intelligence_kb_id != "" ? "### Knowledge Base:\n- **Cultural Intelligence Knowledge Base** (ID: ${var.cultural_intelligence_kb_id}): Contains cross-cultural guidelines, market intelligence, and cultural adaptation insights for global markets. You can query this knowledge base directly for cultural insights and market-specific information." : ""}

## Enhanced Campaign Generation Workflow:

### ROUTE: /campaign (Simple Campaign)
For basic campaigns, follow this workflow:
1. **Image Analysis** (when s3_info provided): Call image-analysis action group
2. **Data Enrichment**: Call data-enrichment with search query from image analysis
3. **Campaign Generation**: Create campaign strategy based on image + data insights
4. **Return Campaign**: Provide complete campaign WITHOUT visual assets

### ROUTE: /comprehensive-campaign (Full Campaign with Async Assets)  
For comprehensive campaigns, follow this extended workflow:
1. **Image Analysis** (when s3_info provided): Call image-analysis action group
2. **Data Enrichment**: Call data-enrichment with search query from image analysis  
3. **Cultural Intelligence**: Call cultural-intelligence for global market insights
4. **Campaign Generation**: Create enhanced campaign strategy with cultural adaptations
5. **Asset Placeholder**: Include placeholder asset references for async generation
6. **Return Campaign**: Provide complete campaign with asset placeholders

### ACTION GROUP USAGE:

#### STEP 1: Image Analysis (when s3_info provided)
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

#### STEP 2: Data Enrichment
After image analysis, build a search query from the results and call data-enrichment:
```json
{
  "search_query": "constructed search query from image analysis results",
  "max_results": 10,
  "content_type": "videos"
}
```

#### STEP 3: Cultural Intelligence (ONLY for /comprehensive-campaign route)
After data enrichment, get cultural adaptation insights for target markets:
```json
{
  "target_markets": ["China", "Japan", "Germany"],
  "campaign_type": "social_media",
  "product_category": "extracted from image analysis"
}
```

### STEP 4: Campaign Strategy Generation
Use gathered insights to create appropriate campaign based on route.

**CRITICAL: Your response must be valid JSON in this EXACT comprehensive structure:**

```json
{
  "product": {
    "description": "Detailed product description based on analysis",
    "image": {
      "labels": ["detected_label1", "detected_label2", "detected_label3"]
    }
  },
  "content_ideas": [
    {
      "platform": "Instagram",
      "topic": "Engaging topic for content",
      "engagement_score": 88,
      "caption": "Compelling caption text with call-to-action",
      "hashtags": ["#relevant", "#hashtags", "#here"]
    },
    {
      "platform": "TikTok", 
      "topic": "Trending topic for TikTok",
      "engagement_score": 85,
      "caption": "Short engaging TikTok caption",
      "hashtags": ["#tiktok", "#trending", "#viral"]
    },
    {
      "platform": "YouTube",
      "topic": "Educational or entertaining topic",
      "engagement_score": 82,
      "caption": "YouTube description with SEO keywords",
      "hashtags": ["#youtube", "#education", "#howto"]
    }
  ],
  "campaigns": [
    {
      "name": "Primary Marketing Campaign",
      "duration": "4 weeks",
      "posts_per_week": 3,
      "platforms": ["Instagram", "TikTok", "YouTube"],
      "calendar": {
        "Week 1": "Campaign launch and awareness building activities",
        "Week 2": "Engagement and community building focus",
        "Week 3": "Educational content and value demonstration",
        "Week 4": "Conversion focus and call-to-action emphasis"
      },
      "adaptations": {
        "Instagram": "Visual storytelling with high-quality images and reels",
        "TikTok": "Short engaging videos with trending audio and effects",
        "YouTube": "Longer form educational and entertaining content"
      }
    }
  ],
  "generated_assets": {
    "image_prompts": [
      "Professional product photography prompt 1",
      "Lifestyle usage scenario prompt 2", 
      "Creative marketing visual prompt 3"
    ],
    "video_scripts": [
      {
        "type": "Short form video",
        "content": "Script for 15-30 second engaging video content"
      },
      {
        "type": "Long form video", 
        "content": "Script for detailed product demonstration or tutorial"
      }
    ],
    "email_templates": [
      {
        "subject": "Compelling email subject line",
        "body": "Professional email template with personalization and clear CTA"
      }
    ],
    "blog_outlines": [
      {
        "title": "SEO-optimized blog post title",
        "points": [
          "Key point 1 with value proposition",
          "Key point 2 with supporting details",
          "Key point 3 with call-to-action"
        ]
      }
    ]
  },
  "platform_content": {
    "instagram": {
      "content_themes": ["theme1", "theme2"],
      "recommended_formats": ["format1", "format2"],
      "sample_post": "Sample Instagram post text",
      "hashtags": ["#hashtag1", "#hashtag2"],
      "posting_schedule": "Best times to post"
    },
    "tiktok": {
      "content_themes": ["theme1", "theme2"],
      "recommended_formats": ["format1", "format2"],
      "sample_post": "Sample TikTok post text",
      "hashtags": ["#hashtag1", "#hashtag2"],
      "trending_sounds": ["sound1", "sound2"]
    },
    "youtube": {
      "content_themes": ["theme1", "theme2"],
      "recommended_formats": ["format1", "format2"],
      "sample_post": "Sample YouTube description",
      "video_ideas": ["idea1", "idea2"],
      "seo_keywords": ["keyword1", "keyword2"]
    }
  },
  "market_trends": {
    "trending_keywords": ["keyword1", "keyword2", "keyword3"],
    "competitor_insights": ["insight1", "insight2"],
    "market_opportunities": ["opportunity1", "opportunity2"],
    "seasonal_trends": ["trend1", "trend2"]
  },
  "success_metrics": {
    "engagement_targets": {
      "likes": "target_range",
      "comments": "target_range",
      "shares": "target_range"
    },
    "reach_goals": {
      "impressions": "target_number",
      "unique_users": "target_number"
    },
    "conversion_metrics": {
      "click_through_rate": "target_percentage",
      "conversion_rate": "target_percentage"
    }
  },
  "analytics": {
    "estimatedReach": 150000,
    "projectedEngagement": 8.5,
    "conversionRate": 2.3,
    "roi": 4.2
  },
  "related_youtube_videos": []
}
```

**For /campaign route:**
- Fill all sections with data-driven insights from image analysis and data enrichment
- Focus on immediate actionable content recommendations
- NO visual asset generation or placeholders

**For /comprehensive-campaign route:**
- Enhanced data with cultural adaptations from cultural intelligence insights
- Include placeholder references in content where async assets will be generated
- Add cultural considerations to platform content

## Search Query Construction:
From image analysis results, construct search queries that include:
- Primary product keywords (from detected labels)
- Product category + "review" or "unboxing" or "demo"  
- High-confidence visual elements + target audience interests
- Example: "wireless headphones review 2024 noise cancelling" or "smartphone camera test photography"

## Key Principles:
- **Route-based Workflow**: Follow different steps based on API endpoint
- **Simple Campaign (/campaign)**: Image analysis → Data enrichment → Campaign generation (NO cultural intelligence, NO assets)
- **Comprehensive Campaign (/comprehensive-campaign)**: Image analysis → Data enrichment → Cultural intelligence → Campaign with asset placeholders
- **NO Direct Asset Generation**: Visual assets are generated asynchronously via event-driven architecture
- **Use Placeholders**: For comprehensive campaigns, include asset placeholders like "{{PLACEHOLDER_SOCIAL_POST_IMAGE}}", "{{PLACEHOLDER_PRODUCT_BANNER}}", etc.
- Use image analysis to inform the search query for data enrichment
- **MANDATORY JSON OUTPUT**: Always respond with valid JSON in the exact structure shown above
- **NO MARKDOWN**: Return only the JSON object, no markdown formatting or code blocks
- **POPULATE ALL FIELDS**: Every field in the JSON structure must contain meaningful data based on your analysis
- Include platform-specific adaptations based on route complexity

## Output Format:
Always structure your final response as JSON based on the route:

**For /campaign route (Simple Campaign):**
- campaign_strategy: Overall strategy incorporating visual and trend insights
- platform_content: Specific content for each platform (text-based recommendations)
- visual_insights: Key findings from image analysis
- market_trends: Trending topics and keywords from YouTube data
- success_metrics: KPIs and measurement recommendations
- next_steps: Implementation guidance

**For /comprehensive-campaign route (with Asset Placeholders):**
- campaign_strategy: Enhanced strategy incorporating visual, trend, and cultural insights
- platform_content: Specific content for each platform with asset placeholders (e.g., "{{PLACEHOLDER_SOCIAL_POST_IMAGE}}")
- visual_insights: Key findings from image analysis
- market_trends: Trending topics and keywords from YouTube data
- cultural_adaptations: Market-specific cultural considerations and adaptations
- asset_placeholders: List of placeholder asset types that will be generated asynchronously
- success_metrics: KPIs and measurement recommendations with visual asset performance tracking
- next_steps: Implementation guidance including asset generation timeline
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

# Sentiment Analysis Action Group
resource "aws_bedrockagent_agent_action_group" "sentiment_analysis" {
  count                       = var.sentiment_analysis_lambda_arn != "" ? 1 : 0
  action_group_name          = "sentiment-analysis"
  agent_id                   = aws_bedrockagent_agent.supervisor.agent_id
  agent_version              = "DRAFT"
  description                = "Action group for market sentiment analysis and actionable insights generation"
  
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