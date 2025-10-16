# Lambda Functions for Bedrock Multi-Agent Architecture

This directory contains Lambda functions that serve as action groups for the Bedrock multi-agent system. Each agent has dedicated Lambda functions that provide specific capabilities.

## Architecture Overview

The multi-agent system consists of:

1. **Campaign Generation Agent** - Creates and optimizes marketing campaigns
2. **Lokalize Agent** - Handles localization and cultural adaptation
3. **Voice of the Market Agent** - Provides market analysis and sentiment insights
4. **Supervisor Agent** - Orchestrates the other agents

## Lambda Function Structure

Each Lambda function follows this structure:

```
lambda/
├── {agent_name}/
│   ├── {function_name}/
│   │   ├── handler.py      # Lambda function code
│   │   └── schema.json     # OpenAPI schema for the action group
```

## Agent Functions

### Campaign Generation Agent

#### Image Analysis (`campaign_generation/image_analysis/`)

- **Purpose**: Analyzes marketing images for visual elements, brand consistency, and cultural sensitivity
- **Key Features**:
  - Visual style detection
  - Color palette analysis
  - Brand element identification
  - Cultural sensitivity scoring
  - Accessibility recommendations

#### Data Enrichment (`campaign_generation/data_enrichment/`)

- **Purpose**: Enriches campaign data with demographic insights, behavioral patterns, and market trends
- **Key Features**:
  - Demographic analysis
  - Behavioral pattern identification
  - Market trend integration
  - Personalization opportunities
  - Competitive landscape insights

### Lokalize Agent

#### Cultural Adaptation (`lokalize_agent/cultural_adaptation/`)

- **Purpose**: Adapts marketing content to align with cultural norms and values of target markets
- **Key Features**:
  - Cultural context analysis
  - Content adaptation recommendations
  - Color symbolism guidance
  - Communication style adjustments
  - Risk assessment for cultural sensitivity

#### Language Translation (`lokalize_agent/language_translation/`)

- **Purpose**: Translates marketing content while preserving brand voice and cultural appropriateness
- **Key Features**:
  - Brand-aware translation
  - Tone preservation
  - Cultural localization
  - Alternative translation options
  - Quality scoring

### Voice of the Market Agent

#### Market Analysis (`voice_of_market/market_analysis/`)

- **Purpose**: Provides comprehensive market analysis including trends, competitive landscape, and opportunities
- **Key Features**:
  - Market size and growth analysis
  - Competitive landscape mapping
  - Consumer segment insights
  - Trend identification
  - SWOT analysis

#### Sentiment Analysis (`voice_of_market/sentiment_analysis/`)

- **Purpose**: Analyzes market sentiment across various channels and sources
- **Key Features**:
  - Multi-channel sentiment monitoring
  - Temporal trend analysis
  - Demographic sentiment breakdown
  - Competitive sentiment comparison
  - Risk indicator identification

## Response Format

All Lambda functions return responses in the Bedrock Agent format:

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": "action_group_name",
    "function": "function_name",
    "functionResponse": {
      "responseBody": {
        "TEXT": {
          "body": "JSON string containing the actual response data"
        }
      }
    }
  }
}
```

## Development Guidelines

### Adding New Functions

1. Create a new directory under the appropriate agent folder
2. Add `handler.py` with the Lambda function code
3. Add `schema.json` with the OpenAPI specification
4. Update the Terraform configuration to include the new function
5. Test the function with sample inputs

### Error Handling

All functions include comprehensive error handling and return structured error responses:

```json
{
  "status": "error",
  "message": "Descriptive error message"
}
```

### Logging

Functions use Python's logging module to log events and errors for debugging and monitoring.

### Environment Variables

Each Lambda function receives these environment variables:

- `AGENT_NAME`: The name of the parent agent
- `FUNCTION_NAME`: The specific function name

## Deployment

The Lambda functions are deployed using Terraform:

1. The functions are packaged as ZIP files
2. IAM roles are created with appropriate permissions
3. Bedrock Agent action groups are configured to use the Lambda functions
4. Permissions are set to allow Bedrock to invoke the functions

## Testing

To test the functions:

1. Use the AWS Lambda console to create test events
2. Use the Bedrock Agent console to test action groups
3. Monitor CloudWatch logs for debugging information

## Security

- Functions run with minimal IAM permissions
- Only Bedrock agents can invoke the functions
- All inputs are validated and sanitized
- Sensitive data is handled according to security best practices
