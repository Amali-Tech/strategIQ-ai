# API Reference

## Base URL

```
https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev
```

## Authentication

Currently, no authentication is required. For production, implement API keys or OAuth 2.0.

## Endpoints

### 1. Generate Campaign

Generate a viral marketing campaign using AI analysis.

**Endpoint**: `POST /api/campaign/tier-1`

**Request Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "product_info": {
    "name": "string (required, 5-200 chars)",
    "description": "string (required, 20-1000 chars)",
    "category": "string (required)",
    "price": "string (optional)",
    "key_features": ["string"] (optional)
  },
  "s3_info": {
    "bucket": "string (required)",
    "key": "string (required)"
  },
  "target_markets": {
    "markets": ["string"] (required, e.g., ["North America", "Europe"])
  },
  "campaign_objectives": {
    "target_audience": "string (required)",
    "target_age_range": "string (optional, e.g., '25-45')",
    "platform_preferences": ["string"] (optional),
    "income_level": "string (optional)",
    "geographic_focus": "string (optional)",
    "campaign_duration": "string (required, e.g., '30 days')",
    "budget": "string (optional, e.g., '$50,000')",
    "primary_goal": "string (required)",
    "secondary_goals": ["string"] (optional)
  }
}
```

**Example Request**:

```bash
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/campaign/tier-1 \
  -H "Content-Type: application/json" \
  -d '{
    "product_info": {
      "name": "Premium Wireless Headphones",
      "description": "High-quality wireless headphones with active noise cancellation",
      "category": "electronics",
      "price": "$299.99",
      "key_features": ["Active Noise Cancellation", "30-hour battery life"]
    },
    "s3_info": {
      "bucket": "degenerals-mi-dev-images",
      "key": "uploads/user123/product.jpg"
    },
    "target_markets": {
      "markets": ["North America", "Europe"]
    },
    "campaign_objectives": {
      "target_audience": "Tech enthusiasts, professionals",
      "target_age_range": "25-55",
      "platform_preferences": ["Instagram", "TikTok", "YouTube"],
      "campaign_duration": "30 days",
      "budget": "$50,000",
      "primary_goal": "Increase brand awareness"
    }
  }'
```

**Success Response** (HTTP 200):

```json
{
  "success": true,
  "correlation_id": "uuid",
  "generation_method": "bedrock_agent_with_tools | fail_safe_orchestration_with_synthesis | fallback_campaign",
  "product_id": "uuid",
  "campaign": {
    "product": {
      "description": "string",
      "image": {
        "public_url": "string",
        "s3_key": "string",
        "labels": [
          {
            "name": "string",
            "confidence": number,
            "categories": ["string"],
            "instances": number
          }
        ]
      }
    },
    "content_ideas": [
      {
        "platform": "Instagram | TikTok | YouTube | LinkedIn | Twitter | Facebook",
        "topic": "string",
        "engagement_score": number (0-100),
        "caption": "string",
        "hashtags": ["string"]
      }
    ],
    "campaigns": [
      {
        "name": "string",
        "duration": "string",
        "posts_per_week": number,
        "platforms": ["string"],
        "calendar": {
          "Week 1": "string",
          "Week 2": "string",
          "Week 3": "string",
          "Week 4": "string"
        },
        "adaptations": {
          "platform": "string"
        },
        "estimated_reach": "string",
        "engagement_score": number
      }
    ],
    "generated_assets": {
      "image_prompts": ["string"],
      "video_scripts": [
        {
          "type": "string",
          "content": "string"
        }
      ],
      "email_templates": [
        {
          "subject": "string",
          "body": "string"
        }
      ],
      "blog_outlines": [
        {
          "title": "string",
          "introduction": "string",
          "points": ["string"]
        }
      ]
    },
    "related_youtube_videos": [
      {
        "video_id": "string",
        "title": "string",
        "channelTitle": "string",
        "thumbnailUrl": "string",
        "viewCount": number,
        "likeCount": number,
        "commentCount": number,
        "url": "string"
      }
    ],
    "platform_recommendations": {
      "primary_platforms": ["string"],
      "rationale": "string"
    },
    "market_insights": {
      "trending_content_types": ["string"],
      "cultural_considerations": ["string"],
      "audience_preferences": ["string"]
    },
    "analytics": {
      "estimatedReach": number,
      "reachChange": "string (e.g., '+12%')",
      "engagementChange": "string (e.g., '+8.5%')",
      "conversionRate": number,
      "estimatedViews": number,
      "projectedShares": number,
      "newFollowers": number
    },
    "recommendations": [
      {
        "type": "timing | content | platform",
        "title": "string",
        "description": "string"
      }
    ]
  }
}
```

**Error Response** (HTTP 500):

```json
{
  "success": false,
  "error": "string",
  "correlation_id": "uuid"
}
```

**Response Time**: 15-25 seconds (typical), 60 seconds (max)

---

### 2. Generate Image (Async)

Submit an image generation request using AI.

**Endpoint**: `POST /api/assets/`

**Request Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "prompt": "string (required, 10-1000 chars)",
  "style": "natural | vivid | anime | photographic (optional, default: natural)",
  "aspect_ratio": "1:1 | 16:9 | 9:16 | 4:3 | 3:4 (optional, default: 1:1)",
  "user_id": "string (optional, default: anonymous)",
  "request_id": "string (optional, auto-generated if not provided)"
}
```

**Example Request**:

```bash
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic cityscape at sunset",
    "style": "vivid",
    "aspect_ratio": "16:9",
    "user_id": "user123",
    "request_id": "req-456"
  }'
```

**Success Response** (HTTP 200):

```json
{
  "message": "Image generation request queued",
  "request_id": "req-456"
}
```

**Error Response** (HTTP 400):

```json
{
  "error": "Prompt is required"
}
```

**Error Response** (HTTP 500):

```json
{
  "message": "Internal Server Error"
}
```

**Response Time**: <1 second (request queued, actual generation is async)

---

### 3. Get Image Generation Status

Check the status of an image generation request.

**Endpoint**: `GET /api/assets/{request_id}`

**Path Parameters**:

- `request_id`: The unique request ID from the generation request

**Example Request**:

```bash
curl -X GET https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/assets/req-456
```

**Success Response - Pending** (HTTP 200):

```json
{
  "request_id": "req-456",
  "status": "pending",
  "user_id": "user123",
  "prompt": "A futuristic cityscape at sunset",
  "style": "vivid",
  "aspect_ratio": "16:9",
  "created_at": "2025-10-19T13:15:00Z"
}
```

**Success Response - Completed** (HTTP 200):

```json
{
  "request_id": "req-456",
  "status": "completed",
  "user_id": "user123",
  "prompt": "A futuristic cityscape at sunset",
  "style": "vivid",
  "aspect_ratio": "16:9",
  "s3_key": "generated/user123/20251019_131530_req-456_A_futuristic_cityscape.png",
  "s3_url": "https://degenerals-mi-dev-generated-assets.s3.amazonaws.com/generated/user123/20251019_131530_req-456_A_futuristic_cityscape.png",
  "created_at": "2025-10-19T13:15:00Z",
  "generated_at": "2025-10-19T13:15:30Z"
}
```

**Success Response - Failed** (HTTP 200):

```json
{
  "request_id": "req-456",
  "status": "failed",
  "error": "Bedrock client error: ...",
  "user_id": "user123",
  "prompt": "A futuristic cityscape at sunset",
  "created_at": "2025-10-19T13:15:00Z"
}
```

**Error Response - Not Found** (HTTP 404):

```json
{
  "error": "Request not found",
  "request_id": "req-456"
}
```

**Response Time**: <100ms

---

### 4. Get Presigned Upload URL

Get a presigned URL for uploading product images to S3.

**Endpoint**: `POST /api/upload/presigned-url`

**Request Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "file_name": "string (required)",
  "file_type": "string (optional, e.g., 'image/jpeg')",
  "user_id": "string (optional, default: anonymous)"
}
```

**Example Request**:

```bash
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/upload/presigned-url \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "product-image.jpg",
    "file_type": "image/jpeg",
    "user_id": "user123"
  }'
```

**Success Response** (HTTP 200):

```json
{
  "upload_url": "https://degenerals-mi-dev-images.s3.amazonaws.com/uploads/user123/20251019_131500_uuid.jpg?X-Amz-Algorithm=...",
  "upload_id": "uuid",
  "s3_key": "uploads/user123/20251019_131500_uuid.jpg",
  "expires_in": 3600
}
```

**Usage**:

```bash
# Upload file using the presigned URL
curl -X PUT "https://degenerals-mi-dev-images.s3.amazonaws.com/..." \
  -H "Content-Type: image/jpeg" \
  --data-binary @product-image.jpg
```

**Response Time**: <200ms

---

### 5. Get Upload Status

Check if a file upload was successful.

**Endpoint**: `GET /api/upload/status/{upload_id}`

**Path Parameters**:

- `upload_id`: The upload ID from the presigned URL response

**Example Request**:

```bash
curl -X GET https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/upload/status/uuid
```

**Success Response - Uploaded** (HTTP 200):

```json
{
  "upload_id": "uuid",
  "status": "completed",
  "s3_key": "uploads/user123/20251019_131500_uuid.jpg",
  "s3_bucket": "degenerals-mi-dev-images"
}
```

**Success Response - Not Found** (HTTP 200):

```json
{
  "upload_id": "uuid",
  "status": "not_found"
}
```

**Response Time**: <200ms

---

## Rate Limits

Currently, no rate limits are enforced. Recommended limits for production:

- Campaign Generation: 10 requests per minute per IP
- Image Generation: 20 requests per minute per user
- Status Checks: 100 requests per minute per user

## Error Codes

| Status Code | Description                             |
| ----------- | --------------------------------------- |
| 200         | Success                                 |
| 400         | Bad Request (invalid input)             |
| 404         | Not Found (resource doesn't exist)      |
| 429         | Too Many Requests (rate limit exceeded) |
| 500         | Internal Server Error                   |
| 503         | Service Unavailable (temporary issue)   |

## SDK Examples

### Python

```python
import requests
import json

BASE_URL = "https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev"

# Generate campaign
def generate_campaign(product_info, s3_info, target_markets, objectives):
    response = requests.post(
        f"{BASE_URL}/api/campaign/tier-1",
        json={
            "product_info": product_info,
            "s3_info": s3_info,
            "target_markets": target_markets,
            "campaign_objectives": objectives
        },
        timeout=65
    )
    return response.json()

# Generate image
def generate_image(prompt, style="vivid", aspect_ratio="16:9"):
    response = requests.post(
        f"{BASE_URL}/api/assets/",
        json={
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio
        }
    )
    return response.json()

# Check image status
def check_image_status(request_id):
    response = requests.get(f"{BASE_URL}/api/assets/{request_id}")
    return response.json()

# Poll for image completion
import time

def wait_for_image(request_id, max_attempts=30, interval=2):
    for _ in range(max_attempts):
        status = check_image_status(request_id)
        if status.get('status') == 'completed':
            return status
        elif status.get('status') == 'failed':
            raise Exception(f"Image generation failed: {status.get('error')}")
        time.sleep(interval)
    raise TimeoutError("Image generation timed out")
```

### JavaScript (Node.js)

```javascript
const axios = require("axios");

const BASE_URL = "https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev";

// Generate campaign
async function generateCampaign(
  productInfo,
  s3Info,
  targetMarkets,
  objectives
) {
  const response = await axios.post(
    `${BASE_URL}/api/campaign/tier-1`,
    {
      product_info: productInfo,
      s3_info: s3Info,
      target_markets: targetMarkets,
      campaign_objectives: objectives,
    },
    {
      timeout: 65000,
    }
  );
  return response.data;
}

// Generate image
async function generateImage(prompt, style = "vivid", aspectRatio = "16:9") {
  const response = await axios.post(`${BASE_URL}/api/assets/`, {
    prompt,
    style,
    aspect_ratio: aspectRatio,
  });
  return response.data;
}

// Check image status
async function checkImageStatus(requestId) {
  const response = await axios.get(`${BASE_URL}/api/assets/${requestId}`);
  return response.data;
}

// Poll for image completion
async function waitForImage(requestId, maxAttempts = 30, interval = 2000) {
  for (let i = 0; i < maxAttempts; i++) {
    const status = await checkImageStatus(requestId);
    if (status.status === "completed") {
      return status;
    } else if (status.status === "failed") {
      throw new Error(`Image generation failed: ${status.error}`);
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
  throw new Error("Image generation timed out");
}
```

### cURL Examples

```bash
# Generate Campaign
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/campaign/tier-1 \
  -H "Content-Type: application/json" \
  -d @campaign-request.json

# Generate Image
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A modern office workspace with plants",
    "style": "natural",
    "aspect_ratio": "16:9"
  }'

# Check Image Status
curl https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/assets/req-123

# Get Presigned Upload URL
curl -X POST https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/upload/presigned-url \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "product.jpg",
    "file_type": "image/jpeg"
  }'

# Upload File to S3
curl -X PUT "https://degenerals-mi-dev-images.s3.amazonaws.com/..." \
  -H "Content-Type: image/jpeg" \
  --data-binary @product.jpg

# Check Upload Status
curl https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev/api/upload/status/uuid
```

## Best Practices

1. **Always handle timeouts**: Campaign generation can take up to 60 seconds
2. **Implement retry logic**: Use exponential backoff for failed requests
3. **Poll efficiently**: Don't poll image status more than once per 2 seconds
4. **Store request IDs**: Always save `request_id` and `correlation_id` for debugging
5. **Validate inputs**: Check field lengths and formats before sending
6. **Handle all status types**: Handle 'pending', 'completed', and 'failed' states
7. **Use HTTPS**: Always use secure connections
8. **Monitor rate limits**: Implement client-side rate limiting

## Webhooks (Future)

Currently, the API requires polling for async operations. Future versions will support webhooks for:

- Image generation completion
- Campaign analysis completion
- Upload confirmation

## Changelog

### Version 1.0.0 (Current)

- Initial API release
- Campaign generation with two-tier architecture
- Async image generation via SQS
- Presigned URL uploads
- Status check endpoints
