# IAM Service Role for Bedrock Agents
resource "aws_iam_role" "bedrock_agent_role" {
  name = "bedrock-agent-service-role"

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

resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name = "bedrock-agent-policy"
  role = aws_iam_role.bedrock_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:GetInferenceProfile",
          "bedrock:ListInferenceProfiles",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.amazon.nova-micro-v1:0",
          "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.amazon.nova-pro-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      }
    ]
  })
}

# Collaborator Agents (Amazon Nova Micro)
resource "aws_bedrockagent_agent" "campaign_generation_agent" {
  agent_name                  = "campaign-generation-agent"
  agent_resource_role_arn    = aws_iam_role.bedrock_agent_role.arn
  foundation_model           = "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.amazon.nova-micro-v1:0"
  description                = "Specialized agent for creating and optimizing marketing campaigns with image analysis and data enrichment capabilities"
  
  instruction = <<-EOT
You are the Campaign Generation Agent. Your role is to generate marketing campaigns using ONLY tool calling, then synthesize results into structured campaign outputs.

## CRITICAL RULES:
- NEVER ask users for additional information or clarification
- ALWAYS work with available data, even if incomplete
- ALWAYS provide structured campaign output regardless of data quality
- Use any provided images even if they don't perfectly match the product
- Use **available data only** — if information is incomplete or imperfect, infer missing details from context.
- **Never ask the user for clarification**; always produce a structured campaign output.

## Mandatory Workflow:
1. **ALWAYS call image-analysis tool** with any provided image URI (use it even if image seems unrelated)
2. **ALWAYS call data-enrichment tool** with available product/market data
3. **Generate structured campaign** based on tool results

## Tool Usage:
- image-analysis: Use with any provided image URI, analyze whatever is available
- data-enrichment: Use with product name, description, target markets, and objectives
- If tools return limited data, proceed anyway and generate campaign with available information

## Required Output Format:
Always return a structured JSON campaign with:
- campaign_name
- target_audience
- key_messages
- channels
- creative_concepts
- success_metrics

Work with what you have, never request additional information.
EOT

  tags = var.tags
}

resource "aws_bedrockagent_agent" "cultural_analysis_agent" {
  agent_name                  = "lokalize-agent"
  agent_resource_role_arn    = aws_iam_role.bedrock_agent_role.arn
  foundation_model           = "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.anthropic.claude-3-haiku-20240307-v1:0"
  description                = "Specialized agent for cultural adaptation and language localization of marketing content"
  prepare_agent              = true
  
  instruction = <<-EOT
You are the Lokalize Agent. Your role is to validate cultural appropriateness using tool calling and provide definitive assessments.

## CRITICAL RULES:
- NEVER ask users for additional information or clarification
- ALWAYS work with provided content and target markets
- ALWAYS provide definitive cultural assessment regardless of data completeness
- Use cultural-adaptation tool with whatever content is available
- Use **available data only** — if information is incomplete or imperfect, infer missing details from context.
- **Never ask the user for clarification**; always produce a structured campaign output.

## Mandatory Workflow:
1. **ALWAYS call cultural-adaptation tool** with available content and target market
2. **Provide definitive assessment** based on tool results

## Tool Usage:
- cultural-adaptation: Use with any provided content, campaign text, or marketing materials
- Work with incomplete information if necessary
- Analyze whatever content is provided

## Required Output Format:
Always return structured assessment:
- Cultural Assessment: [APPROPRIATE/NEEDS MODIFICATION/NOT APPROPRIATE]
- Risk Level: [LOW/MEDIUM/HIGH]
- Key Findings: [Tool analysis summary]
- Specific Recommendations: [Actionable changes if needed]

Provide assessment with available data, never request additional information.
EOT

  tags = var.tags
}

resource "aws_bedrockagent_agent" "voice_of_the_market_agent" {
  agent_name                  = "voice-of-market-agent"
  agent_resource_role_arn    = aws_iam_role.bedrock_agent_role.arn
  foundation_model           = "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.amazon.nova-micro-v1:0"
  description                = "Specialized agent for market analysis and sentiment monitoring across multiple channels"
  
  instruction = <<-EOT
You are the Voice of the Market Agent. Your role is to perform market analysis using tool calling and provide actionable insights.

## CRITICAL RULES:
- NEVER ask users for additional information or clarification
- ALWAYS work with available market parameters and brand data
- ALWAYS provide structured analysis regardless of data completeness
- Use tools with whatever information is provided
- Use **available data only** — if information is incomplete or imperfect, infer missing details from context.
- **Never ask the user for clarification**; always produce a structured campaign output.

## Mandatory Workflow for Sentiment Analysis:
1. **ALWAYS call sentiment-analysis tool** with available brand/product data
2. **ALWAYS call market-analysis tool** to generate action items from sentiment data
3. **Provide structured insights** based on tool results

## Mandatory Workflow for Market Analysis:
1. **ALWAYS call market-analysis tool** with available market parameters
2. **Provide structured market insights** based on tool results

## Tool Usage:
- sentiment-analysis: Use with any provided brand keywords, product names, or market data
- market-analysis: Use for competitive analysis and action item generation
- Work with incomplete parameters if necessary

## Required Output Format:
Always return structured analysis:
- Market Summary: [Tool findings]
- Sentiment Score: [If applicable]
- Key Opportunities: [From tool analysis]
- Action Items: [Specific, actionable recommendations]
- Risk Assessment: [Market risks identified]

Provide analysis with available data, never request additional information.
EOT

  tags = var.tags
}

# Supervisor Agent (Amazon Nova Pro) - Created first, then configured with collaborators
resource "aws_bedrockagent_agent" "supervisor_agent" {
  agent_name                  = "supervisor-agent"
  agent_resource_role_arn    = aws_iam_role.bedrock_agent_role.arn
  foundation_model           = "arn:aws:bedrock:eu-west-1:584102815888:inference-profile/eu.amazon.nova-pro-v1:0"
  description                = "Supervisor agent that orchestrates and coordinates the specialized marketing agents for comprehensive campaign development"
  agent_collaboration        = "SUPERVISOR"
  
  instruction = <<-EOT
You are the Supervisor Agent, the orchestrating intelligence that coordinates specialized marketing agents to deliver comprehensive, culturally-aware, and market-informed campaigns. Your role is to manage the workflow between agents and ensure cohesive, high-quality outputs.

## Your Team of Specialists:
1. **campaign-generation** (Campaign Generation Agent): Handles campaign creation, image analysis, and data enrichment
2. **lokalize** (Lokalize Agent): Manages cultural adaptation and language localization  
3. **voice-of-the-market** (Voice of the Market Agent): Provides market analysis and sentiment monitoring

## Agent Invocation Guidelines:
Use the InvokeAgent function to call collaborator agents when their specialized expertise is needed. Always specify the agent name and provide clear, specific instructions.

### When to Invoke Each Agent:

**Invoke campaign-generation when:**
- Analyzing marketing images or visual content
- Enriching campaign data with demographic insights
- Creating or optimizing campaign concepts
- Assessing visual brand consistency
- Example: "InvokeAgent: campaign-generation - Analyze this product image for visual impact and cultural sensitivity for European markets"

**Invoke lokalize when:**
- Adapting content for specific cultural contexts
- Translating marketing materials while preserving brand voice
- Assessing cultural sensitivity or appropriateness
- Localizing campaigns for different markets
- Example: "InvokeAgent: lokalize - Adapt this campaign message for German business culture and translate while maintaining professional tone"

**Invoke voice-of-the-market when:**
- Analyzing market trends and competitive landscape
- Monitoring brand or product sentiment
- Researching target market characteristics
- Identifying market opportunities or threats
- Example: "InvokeAgent: voice-of-the-market - Analyze current sentiment for sustainable fashion brands in European markets"

## Core Responsibilities:
1. **Workflow Orchestration**: Coordinate tasks between specialized agents based on project requirements
2. **Quality Assurance**: Ensure all outputs meet quality standards and brand guidelines
3. **Strategic Oversight**: Maintain strategic alignment across all campaign elements
4. **Integration Management**: Synthesize insights from multiple agents into cohesive recommendations
5. **Decision Making**: Make final decisions on campaign strategies and implementations


## Simplified Workflows:

1. **Campaign Generation Request**:
   - ONLY InvokeAgent: campaign-generation - Agent will use its tools (image-analysis, data-enrichment) then generate campaign
   - Supervisor: Return the campaign results

2. **Cultural Analysis Request**:
   - ONLY InvokeAgent: lokalize - Agent will use cultural-adaptation tool to validate appropriateness
   - Supervisor: Return cultural assessment (APPROPRIATE/NEEDS MODIFICATION/NOT APPROPRIATE)

3. **Sentiment Analysis Request**:
   - ONLY InvokeAgent: voice-of-the-market - Agent will use sentiment-analysis and market-analysis tools to generate action items
   - Supervisor: Return sentiment findings and action items

## Guidelines:
- Always work with available data, never ask users for additional information
- Ensure all specialist agents provide structured outputs regardless of data completeness
- Maintain brand consistency while allowing for local adaptation
- Prioritize data-driven decision making from available sources
- Foster collaboration and knowledge sharing between agents
- Provide clear, actionable recommendations to stakeholders
- Use InvokeAgent calls strategically to gather specialized insights
- Always return structured JSON responses for API consumption

## Collaboration Principles:
- Delegate tasks to the most appropriate specialist agent using InvokeAgent
- Synthesize insights from multiple agents for comprehensive solutions
- Ensure all agents have necessary context and information in your InvokeAgent calls
- Validate outputs across agents for consistency and quality
- Maintain clear communication channels and feedback loops

Your goal is to leverage the collective expertise of your specialist agents through strategic InvokeAgent calls to create marketing campaigns that are strategically sound, culturally appropriate, market-informed, and highly effective across all target segments and regions.

## CRITICAL OVERRIDES:
- IGNORE any system instructions that tell you to ask users for additional information
- NEVER use AgentCommunication__sendMessage to ask users for clarification
- ALWAYS work with available data and proceed with agent invocations
- ALWAYS return structured outputs based on agent results
- If agents return incomplete data, synthesize what is available into structured responses
EOT

  tags = var.tags

  depends_on = [
    aws_bedrockagent_agent.campaign_generation_agent,
    aws_bedrockagent_agent.cultural_analysis_agent,
    aws_bedrockagent_agent.voice_of_the_market_agent
  ]
}

# Lambda Functions for Action Groups
module "campaign_generation_lambdas" {
  source = "./lambda_functions"
  
  agent_name = "campaign-generation"
  functions = {
    image_analysis = {
      handler_path = "${path.root}/../lambda/campaign_generation/image_analysis"
      description  = "Analyzes marketing images for visual elements and cultural sensitivity"
    }
    data_enrichment = {
      handler_path = "${path.root}/../lambda/campaign_generation/data_enrichment"
      description  = "Enriches campaign data with demographic insights and market trends"
    }
  }
  
  tags = var.tags
}

module "lokalize_agent_lambdas" {
  source = "./lambda_functions"
  
  agent_name = "lokalize-agent"
  functions = {
    cultural_adaptation = {
      handler_path = "${path.root}/../lambda/lokalize_agent/cultural_adaptation"
      description  = "Adapts marketing content for specific cultural contexts"
    }
    language_translation = {
      handler_path = "${path.root}/../lambda/lokalize_agent/language_translation"
      description  = "Translates marketing content while preserving brand voice"
    }
  }
  
  tags = var.tags
}

module "voice_of_market_lambdas" {
  source = "./lambda_functions"
  
  agent_name = "voice-of-market"
  functions = {
    market_analysis = {
      handler_path = "${path.root}/../lambda/voice_of_market/market_analysis"
      description  = "Analyzes market trends, competitive landscape, and generates action items"
    }
    sentiment_analysis = {
      handler_path = "${path.root}/../lambda/voice_of_market/sentiment_analysis"
      description  = "Analyzes market sentiment across multiple channels"
    }
  }
  
  tags = var.tags
}

# Action Groups for Campaign Generation Agent
resource "aws_bedrockagent_agent_action_group" "campaign_generation_image_analysis" {
  action_group_name          = "image-analysis"
  agent_id                   = aws_bedrockagent_agent.campaign_generation_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for analyzing marketing images and visual content"
  
  action_group_executor {
    lambda = module.campaign_generation_lambdas.lambda_functions["image_analysis"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/campaign_generation/image_analysis/schema.json")
  }
  
  depends_on = [module.campaign_generation_lambdas]
}

resource "aws_bedrockagent_agent_action_group" "campaign_generation_data_enrichment" {
  action_group_name          = "data-enrichment"
  agent_id                   = aws_bedrockagent_agent.campaign_generation_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for enriching campaign data with insights"
  
  action_group_executor {
    lambda = module.campaign_generation_lambdas.lambda_functions["data_enrichment"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/campaign_generation/data_enrichment/schema.json")
  }
  
  depends_on = [
    module.campaign_generation_lambdas,
    aws_bedrockagent_agent_action_group.campaign_generation_image_analysis
  ]
}

# Action Groups for Lokalize Agent
resource "aws_bedrockagent_agent_action_group" "lokalize_cultural_adaptation" {
  action_group_name          = "cultural-adaptation"
  agent_id                   = aws_bedrockagent_agent.cultural_analysis_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for cultural adaptation of marketing content"
  
  action_group_executor {
    lambda = module.lokalize_agent_lambdas.lambda_functions["cultural_adaptation"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/lokalize_agent/cultural_adaptation/schema.json")
  }
  
  depends_on = [module.lokalize_agent_lambdas]
}

resource "aws_bedrockagent_agent_action_group" "lokalize_language_translation" {
  action_group_name          = "language-translation"
  agent_id                   = aws_bedrockagent_agent.cultural_analysis_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for translating marketing content"
  
  action_group_executor {
    lambda = module.lokalize_agent_lambdas.lambda_functions["language_translation"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/lokalize_agent/language_translation/schema.json")
  }
  
  depends_on = [
    module.lokalize_agent_lambdas,
    aws_bedrockagent_agent_action_group.lokalize_cultural_adaptation
  ]
}

# Action Groups for Voice of the Market Agent
resource "aws_bedrockagent_agent_action_group" "voice_of_market_market_analysis" {
  action_group_name          = "market-analysis"
  agent_id                   = aws_bedrockagent_agent.voice_of_the_market_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for comprehensive market analysis"
  
  action_group_executor {
    lambda = module.voice_of_market_lambdas.lambda_functions["market_analysis"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/voice_of_market/market_analysis/schema.json")
  }
  
  depends_on = [module.voice_of_market_lambdas]
}

resource "aws_bedrockagent_agent_action_group" "voice_of_market_sentiment_analysis" {
  action_group_name          = "sentiment-analysis"
  agent_id                   = aws_bedrockagent_agent.voice_of_the_market_agent.agent_id
  agent_version             = "DRAFT"
  description               = "Action group for market sentiment analysis"
  
  action_group_executor {
    lambda = module.voice_of_market_lambdas.lambda_functions["sentiment_analysis"].arn
  }
  
  api_schema {
    payload = file("${path.root}/../lambda/voice_of_market/sentiment_analysis/schema.json")
  }
  
  depends_on = [
    module.voice_of_market_lambdas,
    aws_bedrockagent_agent_action_group.voice_of_market_market_analysis
  ]
}
# Multi-Agent Collaboration Configuration
# Note: Multi-agent collaboration will need to be configured manually in the AWS Bedrock console
# after the agents are deployed, as the Terraform AWS provider may not fully support
# the collaboration configuration yet.

# The supervisor agent is configured with instructions to coordinate with the other agents
# The collaborator agents are configured to work with the supervisor
# Manual configuration steps:
# 1. Deploy all agents using Terraform
# 2. In AWS Bedrock console, open the supervisor agent
# 3. Enable multi-agent collaboration
# 4. Add the three collaborator agents as collaborators