# Campaign Generation Workflow

## Overview

The campaign generation system uses a **two-tier architecture** with intelligent fallback to ensure reliability.

## Workflow Diagram

```
Client Request
     ↓
API Gateway (POST /api/campaign/tier-1)
     ↓
Intent Parser Lambda
     ↓
┌────────────────────────────────────────┐
│  TIER 1: Bedrock Agent with Tools      │
│  (Primary Path)                        │
└────────────────────────────────────────┘
     ↓ (if successful)
     ├─→ Return Campaign JSON
     ↓ (if failed)
┌────────────────────────────────────────┐
│  TIER 2: Sequential Lambda Invocation  │
│  (Fallback Path)                       │
└────────────────────────────────────────┘
     ↓
     ├─→ Image Analysis Lambda
     ├─→ Data Enrichment Lambda
     ├─→ Cultural Intelligence Lambda
     ↓
  Aggregate Results in DynamoDB
     ↓
  Bedrock Generation from data
     ↓
  Return Campaign JSON
```

## Detailed Flow

### Step 1: Client Request

**Endpoint**: `POST /api/campaign/tier-1`

**Request Body**:

```json
{
  "product_info": {
    "name": "Premium Wireless Headphones",
    "description": "High-quality wireless headphones...",
    "category": "electronics",
    "price": "$299.99",
    "key_features": ["ANC", "30-hour battery", "Bluetooth 5.0"]
  },
  "s3_info": {
    "bucket": "degenerals-mi-dev-images",
    "key": "uploads/user123/product.jpg"
  },
  "target_markets": {
    "markets": ["North America", "Europe", "Asia"]
  },
  "campaign_objectives": {
    "target_audience": "Tech enthusiasts, professionals",
    "target_age_range": "25-55",
    "platform_preferences": ["Instagram", "TikTok", "YouTube"],
    "campaign_duration": "30 days",
    "budget": "$50,000",
    "primary_goal": "Increase brand awareness"
  }
}
```

### Step 2: Intent Parser Orchestration

The `intent-parser-lambda` receives the request and generates a correlation ID for tracking.

```python
correlation_id = str(uuid.uuid4())
```

### Step 3: TIER 1 - Bedrock Agent with Tool Calling

#### Attempt

```python
try_bedrock_agent_with_tools(
    product_info,
    s3_info,
    target_markets,
    campaign_objectives,
    correlation_id
)
```

#### Agent Configuration

- **Agent ID**: From `BEDROCK_AGENT_ID` environment variable
- **Alias ID**: From `BEDROCK_AGENT_ALIAS_ID` environment variable
- **Session ID**: `session-{correlation_id}`

#### Agent Tools

The Bedrock agent has access to three Lambda tools:

1. **analyzeProductImage** → `image-analysis-lambda`
2. **enrichProductData** → `data-enrichment-lambda`
3. **getCulturalIntelligence** → `cultural-intelligence-lambda`

#### Success Criteria

- Agent returns valid JSON matching campaign schema
- Response contains all required fields
- No exceptions during invocation

#### Failure Triggers

- ResourceNotFoundException (agent doesn't exist)
- Timeout (>60 seconds)
- Invalid JSON response
- Missing required fields

### Step 4: TIER 2 - Fail-Safe Orchestration

If TIER 1 fails, the system falls back to sequential Lambda invocation.

#### 4.1 Image Analysis

**Invocation**:

```python
invoke_lambda_sync('image-analysis-lambda', {
    "s3_bucket": s3_info["bucket"],
    "s3_key": s3_info["key"],
    "product_info": product_info
})
```

**Purpose**:

- Extract visual features from product image
- Detect objects, labels, and categories
- Store results in DynamoDB

**Output**:

```json
{
  "product_id": "uuid",
  "user_id": "anonymous",
  "labels": [
    { "name": "Electronics", "confidence": 99.98 },
    { "name": "Headphones", "confidence": 99.97 }
  ]
}
```

#### 4.2 Data Enrichment

**Invocation**:

```python
invoke_lambda_sync('data-enrichment-lambda', {
    "product_id": product_id,
    "product_name": product_info["name"],
    "category": product_info["category"]
})
```

**Purpose**:

- Search YouTube for related product videos
- Extract engagement metrics
- Identify trending content

**Output**:

```json
{
  "youtube_videos": [
    {
      "title": "Best Headphones 2025",
      "channelTitle": "Tech Review",
      "viewCount": 100000,
      "likeCount": 8500,
      "commentCount": 450,
      "thumbnailUrl": "https://...",
      "url": "https://youtube.com/watch?v=..."
    }
  ]
}
```

#### 4.3 Cultural Intelligence

**Invocation**:

```python
invoke_lambda_sync('cultural-intelligence-lambda', {
    "product_id": product_id,
    "markets": target_markets["markets"],
    "product_category": product_info["category"]
})
```

**Purpose**:

- Provide market-specific insights
- Cultural considerations
- Regional preferences

**Output**:

```json
{
  "market_insights": {
    "North America": {
      "preferences": ["Premium quality", "Brand reputation"],
      "platforms": ["Instagram", "TikTok"],
      "content_types": ["Unboxing", "Reviews"]
    }
  }
}
```

#### 4.4 Data Aggregation

All Lambda results are stored in DynamoDB under `product_id`:

```python
table.update_item(
    Key={'product_id': product_id},
    UpdateExpression='SET image_analysis = :ia, youtube_data = :yd, cultural_data = :cd',
    ExpressionAttributeValues={
        ':ia': image_analysis_result,
        ':yd': enrichment_result,
        ':cd': cultural_result
    }
)
```

#### 4.5 Bedrock Synthesis

**Model**: Amazon Nova Pro
**Inference Config**:

```python
{
    'maxTokens': 4096  # Allows complete campaign JSON
}
```

**Prompt Structure**:

```
You are a viral marketing campaign expert. Based on the complete market analysis data provided, synthesize a comprehensive marketing campaign strategy.

Product: {product_name}
Product ID: {product_id}

Image Analysis: {...}
YouTube Trends: {...}
Market Insights: {...}
Campaign Objectives: {...}

Return ONLY valid JSON matching this EXACT schema...
```

**Response Extraction**:

```python
response_body = json.loads(response['body'].read())
campaign_json = extract_campaign_json(response_body['content'][0]['text'])
```

### Step 5: Fallback Campaign

If Bedrock synthesis also fails (JSON parse error, timeout, etc.), the system generates a hardcoded fallback campaign:

```python
create_fallback_campaign(aggregated_record, campaign_objectives)
```

This ensures the client always receives a valid response.

### Step 6: Response

**Success Response** (HTTP 200):

```json
{
  "success": true,
  "correlation_id": "uuid",
  "generation_method": "bedrock_agent_with_tools" | "fail_safe_orchestration_with_synthesis" | "fallback_campaign",
  "product_id": "uuid",
  "campaign": {
    "product": {...},
    "content_ideas": [...],
    "campaigns": [...],
    "generated_assets": {...},
    "related_youtube_videos": [...],
    "platform_recommendations": {...},
    "market_insights": {...},
    "analytics": {...},
    "recommendations": [...]
  }
}
```

**Error Response** (HTTP 500):

```json
{
  "success": false,
  "error": "Error message",
  "correlation_id": "uuid"
}
```

## Campaign JSON Schema

See [Campaign Schema Reference](./campaign-schema.md) for complete field definitions.

## Performance Metrics

- **TIER 1 Success Rate**: ~60%
- **TIER 2 Success Rate**: ~95%
- **Average Duration**: 15-40 seconds
- **Timeout**: 60 seconds

## Error Handling

### Retry Strategy

- Retries with exponential back-off for bedrock agent orchestration flow
- Correlation ID for tracking

### Logging

All stages logged to CloudWatch:

```
TIER 1: Attempting Bedrock agent...
TIER 1 FAILED: {reason}
TIER 2: Using fail-safe orchestration...
TIER 2 SUCCESS: Bedrock synthesized campaign
```
