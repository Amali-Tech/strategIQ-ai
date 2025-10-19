# Data Flow and Integration

## Overview

This document details how data flows through the system, including integrations between components, data transformations, and storage patterns.

## System Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATION                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (HTTP API v2)                           │
│  • POST /api/campaign/tier-1                                                 │
│  • POST /api/assets/                                                         │
│  • GET /api/assets/{request_id}                                              │
│  • POST /api/upload/presigned-url                                            │
│  • GET /api/upload/status/{upload_id}                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
    ┌───────────────────────────┐   ┌──────────────────────────┐
    │   LAMBDA FUNCTIONS        │   │   SQS INTEGRATION        │
    │   • Intent Parser         │   │   • Send to Queue        │
    │   • Image Status          │   └──────────────────────────┘
    │   • Upload Handler        │                │
    └───────────────────────────┘                ▼
                    │                 ┌──────────────────────────┐
                    ▼                 │   SQS QUEUE              │
    ┌───────────────────────────┐    │   • Image Generation     │
    │   ORCHESTRATION           │    └──────────────────────────┘
    │   • Sequential Lambdas    │                │
    │   • Data Aggregation      │                ▼
    └───────────────────────────┘    ┌──────────────────────────┐
                    │                 │   Generate Images Lambda │
                    ▼                 └──────────────────────────┘
    ┌───────────────────────────┐                │
    │   AI/ML SERVICES          │                │
    │   • Bedrock (Nova)        │◄───────────────┘
    │   • Rekognition           │
    └───────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │   DATA STORAGE                                │
    │   • DynamoDB (products, generated_images)     │
    │   • S3 (images, generated assets)             │
    └───────────────────────────────────────────────┘
```

## Data Flow Patterns

### Pattern 1: Campaign Generation (Synchronous)

```
Client → API Gateway → Intent Parser Lambda
                            │
                            ├─→ TIER 1: Bedrock Agent (if available)
                            │   └─→ Agent invokes Lambda tools automatically
                            │
                            └─→ TIER 2: Sequential Processing (fallback)
                                ├─→ Image Analysis Lambda
                                │   ├─→ S3: Read product image
                                │   ├─→ Rekognition: Analyze image
                                │   └─→ DynamoDB: Store results
                                │
                                ├─→ Data Enrichment Lambda
                                │   ├─→ YouTube API: Search videos
                                │   └─→ DynamoDB: Update record
                                │
                                ├─→ Cultural Intelligence Lambda
                                │   ├─→ Bedrock: Generate insights
                                │   └─→ DynamoDB: Update record
                                │
                                ├─→ DynamoDB: Read aggregated data
                                ├─→ Bedrock Nova Pro: Synthesize campaign
                                └─→ Return campaign JSON
```

**Characteristics**:

- Synchronous request/response
- 15-20 second typical duration
- 60 second timeout
- Sequential Lambda invocations
- Single DynamoDB product record

### Pattern 2: Image Generation (Asynchronous)

```
Client → API Gateway → SQS → Generate Images Lambda → Bedrock Nova Canvas
                                        │
                                        ├─→ S3: Store generated image
                                        └─→ DynamoDB: Update status

Client → API Gateway → Image Status Lambda → DynamoDB: Query status
                                        └─→ Return status + S3 URL
```

**Characteristics**:

- Asynchronous message queue
- Decoupled request/response
- 3-5 second generation time
- Client polls for status
- Separate DynamoDB table

### Pattern 3: Product Image Upload (Pre-signed URL)

```
Client → API Gateway → Upload Handler Lambda → S3: Generate presigned URL
                                        └─→ Return presigned URL

Client → S3: Upload image directly (using presigned URL)

Client → API Gateway → Upload Status Lambda → S3: Check object existence
                                        └─→ Return upload status
```

**Characteristics**:

- Direct S3 upload
- No Lambda processing during upload
- Presigned URL expires in 1 hour
- Status check via S3 HeadObject

## Data Storage Schemas

### DynamoDB Table: `products`

**Partition Key**: `product_id` (String)

**Attributes**:

```json
{
  "product_id": "uuid",
  "user_id": "string",
  "product_name": "string",
  "product_description": "string",
  "s3_bucket": "string",
  "s3_key": "string",
  "upload_timestamp": "ISO-8601 string",

  // Image Analysis Results
  "image_analysis": {
    "labels": [
      {
        "name": "string",
        "confidence": number,
        "categories": ["string"],
        "instances": number
      }
    ],
    "analyzed_at": "ISO-8601 string"
  },

  // YouTube Data Enrichment
  "youtube_data": {
    "videos": [
      {
        "video_id": "string",
        "title": "string",
        "channel_title": "string",
        "description": "string",
        "published_at": "ISO-8601 string",
        "thumbnail_url": "string",
        "viewCount": number,
        "likeCount": number,
        "commentCount": number,
        "relevance_score": number,
        "url": "string"
      }
    ],
    "enriched_at": "ISO-8601 string"
  },

  // Cultural Intelligence
  "cultural_data": {
    "market_insights": {
      "region_name": {
        "preferences": ["string"],
        "platforms": ["string"],
        "content_types": ["string"],
        "cultural_notes": "string"
      }
    },
    "analyzed_at": "ISO-8601 string"
  },

  // Campaign Generation
  "campaign": {
    "correlation_id": "uuid",
    "generation_method": "string",
    "generated_at": "ISO-8601 string",
    "campaign_data": {
      // Full campaign JSON
    }
  }
}
```

**Access Patterns**:

1. **Get by product_id**: `GetItem` - Primary lookup
2. **Update analysis results**: `UpdateItem` - Partial updates
3. **Query by user_id**: Requires GSI (not currently implemented)

**Indexes**:

- Primary: `product_id` (Partition Key only)
- Future: GSI on `user_id` for user-specific queries

### DynamoDB Table: `generated_images`

**Partition Key**: `request_id` (String)

**Attributes**:

```json
{
  "request_id": "string (uuid)",
  "user_id": "string",
  "prompt": "string",
  "style": "string",
  "aspect_ratio": "string",
  "status": "pending | completed | failed",

  // For completed images
  "s3_key": "string",
  "s3_url": "string",
  "generated_at": "ISO-8601 string",

  // For failed images
  "error": "string",

  // Timestamps
  "created_at": "ISO-8601 string"
}
```

**Access Patterns**:

1. **Get status by request_id**: `GetItem` - Status polling
2. **List by user_id**: Requires GSI (not currently implemented)

**TTL**: Not configured (consider for old records)

### S3 Bucket: `degenerals-mi-dev-images`

**Purpose**: Product image uploads

**Structure**:

```
uploads/
  ├── anonymous/
  │   └── {timestamp}_{uuid}.{ext}
  └── {user_id}/
      └── {timestamp}_{uuid}.{ext}
```

**Access**:

- Private bucket
- Presigned URLs for upload
- Lambda reads via IAM role

**Lifecycle**:

- No automatic deletion
- Consider lifecycle policy for old uploads

### S3 Bucket: `degenerals-mi-dev-generated-assets`

**Purpose**: AI-generated marketing assets

**Structure**:

```
generated/
  ├── anonymous/
  │   └── {timestamp}_{request_id}_{sanitized_prompt}.png
  └── {user_id}/
      └── {timestamp}_{request_id}_{sanitized_prompt}.png
```

**Access**:

- Public read via bucket policy
- Direct HTTPS URLs

**Bucket Policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::degenerals-mi-dev-generated-assets/*"
    }
  ]
}
```

## Integration Details

### Integration 1: Lambda → Bedrock

**Service**: Amazon Bedrock Runtime API

**Models Used**:

1. **Nova Pro** (`arn:aws:bedrock:eu-west-1::inference-profile/eu.amazon.nova-pro-v1:0`)
2. **Nova Canvas** (`amazon.nova-canvas-v1:0`)

**Request Format (Nova Pro)**:

```python
bedrock_client.invoke_model(
    modelId='arn:aws:bedrock:eu-west-1::inference-profile/eu.amazon.nova-pro-v1:0',
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        'messages': [
            {
                'role': 'user',
                'content': [{'text': prompt}]
            }
        ],
        'inferenceConfig': {
            'maxTokens': 4096
        }
    })
)
```

**Response Format**:

```json
{
  "output": {
    "message": {
      "role": "assistant",
      "content": [
        {
          "text": "JSON campaign data..."
        }
      ]
    }
  },
  "stopReason": "end_turn | max_tokens",
  "usage": {
    "inputTokens": 4257,
    "outputTokens": 2048,
    "totalTokens": 6305
  }
}
```

**Request Format (Nova Canvas)**:

```python
bedrock_client.invoke_model(
    modelId='amazon.nova-canvas-v1:0',
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        'taskType': 'TEXT_IMAGE',
        'textToImageParams': {
            'text': prompt,
            'negativeText': 'blurry, low quality'
        },
        'imageGenerationConfig': {
            'numberOfImages': 1,
            'quality': 'standard',
            'width': 1280,
            'height': 720,
            'cfgScale': 7.0
        }
    })
)
```

**Response Format**:

```json
{
  "images": ["base64_encoded_image_data..."]
}
```

### Integration 2: Lambda → Rekognition

**Service**: AWS Rekognition

**Operation**: `detect_labels`

**Request**:

```python
rekognition_client.detect_labels(
    Image={
        'S3Object': {
            'Bucket': bucket,
            'Name': key
        }
    },
    MaxLabels=50,
    MinConfidence=75
)
```

**Response**:

```json
{
  "Labels": [
    {
      "Name": "Electronics",
      "Confidence": 99.98,
      "Instances": [],
      "Parents": [{ "Name": "Technology and Computing" }],
      "Aliases": [],
      "Categories": [{ "Name": "Technology and Computing" }]
    }
  ]
}
```

### Integration 3: Lambda → YouTube Data API

**Service**: YouTube Data API v3

**Endpoint**: `https://www.googleapis.com/youtube/v3/search`

**Request**:

```python
params = {
    'part': 'snippet',
    'q': f"{product_name} {category} review",
    'type': 'video',
    'maxResults': 10,
    'order': 'relevance',
    'key': YOUTUBE_API_KEY
}
```

**Response**:

```json
{
  "items": [
    {
      "id": { "videoId": "string" },
      "snippet": {
        "title": "string",
        "description": "string",
        "channelTitle": "string",
        "publishedAt": "ISO-8601",
        "thumbnails": {
          "default": { "url": "string" }
        }
      }
    }
  ]
}
```

**Video Statistics** (separate call):

```python
# Get video statistics
params = {
    'part': 'statistics',
    'id': video_id,
    'key': YOUTUBE_API_KEY
}
```

**Statistics Response**:

```json
{
  "items": [
    {
      "statistics": {
        "viewCount": "100000",
        "likeCount": "8500",
        "commentCount": "450"
      }
    }
  ]
}
```

### Integration 4: API Gateway → SQS

**Integration Type**: AWS Service Integration (non-proxy)

**Action**: `SendMessage`

**Request Template**:

```
Action=SendMessage&MessageBody=$util.urlEncode($input.body)
```

**Response Template**:

```json
{
  "message": "Image generation request queued",
  "request_id": "$input.path('$.request_id')"
}
```

**IAM Execution Role**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Integration 5: Lambda → DynamoDB

**Operations Used**:

1. **PutItem**: Store new records
2. **GetItem**: Retrieve by key
3. **UpdateItem**: Partial updates
4. **Query**: Not currently used (requires GSI)

**Example - Store Product**:

```python
table.put_item(
    Item={
        'product_id': product_id,
        'user_id': user_id,
        'product_name': name,
        'upload_timestamp': datetime.now().isoformat()
    }
)
```

**Example - Update with Analysis**:

```python
table.update_item(
    Key={'product_id': product_id},
    UpdateExpression='SET image_analysis = :analysis',
    ExpressionAttributeValues={
        ':analysis': analysis_data
    }
)
```

**Example - Conditional Update**:

```python
table.update_item(
    Key={'request_id': request_id},
    UpdateExpression='SET #status = :status, s3_url = :url',
    ConditionExpression='attribute_exists(request_id)',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':status': 'completed',
        ':url': s3_url
    }
)
```

## Data Transformation Patterns

### Pattern 1: YouTube Data Enrichment

**Input** (YouTube API):

```json
{
  "id": { "videoId": "abc123" },
  "snippet": {
    "title": "Product Review",
    "channelTitle": "Tech Channel",
    "thumbnails": {
      "default": { "url": "https://..." }
    }
  }
}
```

**Transformation**:

```python
video = {
    'video_id': item['id']['videoId'],
    'title': item['snippet']['title'],
    'channel_title': item['snippet']['channelTitle'],
    'channelTitle': item['snippet']['channelTitle'],  # Alias for frontend
    'description': item['snippet'].get('description', ''),
    'published_at': item['snippet']['publishedAt'],
    'thumbnail_url': item['snippet']['thumbnails']['default']['url'],
    'thumbnailUrl': item['snippet']['thumbnails']['default']['url'],  # Alias
    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
}

# Merge with statistics
video.update({
    'viewCount': int(stats.get('viewCount', 0)),
    'likeCount': int(stats.get('likeCount', 0)),
    'commentCount': int(stats.get('commentCount', 0)),
    'relevance_score': calculate_relevance(video)
})
```

**Output** (Stored in DynamoDB):

```json
{
  "video_id": "abc123",
  "title": "Product Review",
  "channelTitle": "Tech Channel",
  "thumbnailUrl": "https://...",
  "viewCount": 100000,
  "likeCount": 8500,
  "commentCount": 450,
  "relevance_score": 85,
  "url": "https://www.youtube.com/watch?v=abc123"
}
```

### Pattern 2: Rekognition Label Processing

**Input** (Rekognition):

```json
{
  "Name": "Electronics",
  "Confidence": 99.98,
  "Instances": [],
  "Parents": [{ "Name": "Technology and Computing" }],
  "Categories": [{ "Name": "Technology and Computing" }]
}
```

**Transformation**:

```python
label = {
    'name': rekognition_label['Name'],
    'confidence': rekognition_label['Confidence'],
    'categories': [cat['Name'] for cat in rekognition_label.get('Categories', [])],
    'instances': len(rekognition_label.get('Instances', []))
}
```

**Output** (Stored in DynamoDB):

```json
{
  "name": "Electronics",
  "confidence": 99.98,
  "categories": ["Technology and Computing"],
  "instances": 0
}
```

### Pattern 3: Bedrock Response Extraction

**Input** (Bedrock Nova Pro):

```json
{
  "output": {
    "message": {
      "content": [
        {
          "text": "{\"product\": {...}, \"campaigns\": [...]}"
        }
      ]
    }
  }
}
```

**Transformation**:

```python
def extract_campaign_json(response_text):
    # Try to find JSON in response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        return json.loads(json_str)
    return None
```

**Output** (Campaign JSON):

```json
{
  "product": {...},
  "content_ideas": [...],
  "campaigns": [...],
  "generated_assets": {...}
}
```

## Error Handling and Retry Logic

### SQS Message Retry

**Configuration**:

- Max receive count: 3
- Visibility timeout: 300 seconds
- Dead Letter Queue: Configured

**Retry Scenarios**:

1. **Transient Bedrock Error**: Message reprocessed after visibility timeout
2. **S3 Access Error**: Message reprocessed up to 3 times
3. **Max Retries Exceeded**: Message moved to DLQ

### Lambda Synchronous Retry

**Pattern**: No automatic retry for synchronous Lambda invocations

**Client Responsibility**:

```python
# Client should implement retry with exponential backoff
import time

def invoke_with_retry(function_name, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            return lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
        except ClientError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### DynamoDB Conditional Write

**Pattern**: Optimistic locking for concurrent updates

```python
try:
    table.update_item(
        Key={'request_id': request_id},
        UpdateExpression='SET #status = :new_status',
        ConditionExpression='#status = :expected_status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':new_status': 'completed',
            ':expected_status': 'pending'
        }
    )
except ClientError as e:
    if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        # Status already updated by another process
        pass
```

## Performance Optimization

### Lambda Cold Start Mitigation

**Strategy**: Provisioned concurrency for high-traffic functions

```hcl
resource "aws_lambda_provisioned_concurrency_config" "intent_parser" {
  function_name                     = aws_lambda_function.intent_parser.function_name
  provisioned_concurrent_executions = 2
  qualifier                         = aws_lambda_alias.intent_parser_live.name
}
```

### DynamoDB Read/Write Optimization

**Current**: On-demand capacity mode

**Optimization**:

```python
# Batch writes for multiple items
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)
```

### S3 Transfer Acceleration

**Not Currently Enabled**

**Future Enhancement**:

```python
s3_client = boto3.client(
    's3',
    config=Config(s3={'use_accelerate_endpoint': True})
)
```

## Data Governance

### Data Retention

**Products Table**:

- Retention: Indefinite
- Consideration: Implement TTL for old products

**Generated Images Table**:

- Retention: Indefinite
- Consideration: Implement TTL after 30 days

**S3 Objects**:

- Retention: Indefinite
- Consideration: Lifecycle policy to Glacier after 90 days

### Data Privacy

**PII Handling**:

- User IDs are opaque identifiers
- No email/name stored in system
- S3 keys do not contain PII

**GDPR Compliance**:

- Right to deletion: Manual S3/DynamoDB cleanup
- Data portability: DynamoDB export feature

## Monitoring and Observability

### CloudWatch Metrics

**Lambda Metrics**:

- Invocations
- Errors
- Duration
- Throttles
- Concurrent executions

**DynamoDB Metrics**:

- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors

**SQS Metrics**:

- NumberOfMessagesSent
- NumberOfMessagesReceived
- ApproximateAgeOfOldestMessage
- NumberOfMessagesDeleted

### Custom Metrics

**Campaign Generation**:

```python
cloudwatch.put_metric_data(
    Namespace='Degenerals/Campaigns',
    MetricData=[
        {
            'MetricName': 'GenerationMethod',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Method', 'Value': 'bedrock_agent'}
            ]
        }
    ]
)
```

### Distributed Tracing

**X-Ray Integration**:

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

@xray_recorder.capture('synthesize_campaign')
def synthesize_with_bedrock(product_id, data, objectives):
    # Function logic
    pass
```

## Cost Optimization

### Bedrock Pricing

**Nova Pro**:

- Input: $0.80 per 1M tokens
- Output: $3.20 per 1M tokens
- Avg campaign: ~4000 input + ~2000 output tokens
- Cost per campaign: ~$0.01

**Nova Canvas**:

- Standard quality: ~$0.04 per image
- Premium quality: ~$0.08 per image

### DynamoDB Pricing

**On-Demand Mode**:

- Write: $1.25 per million requests
- Read: $0.25 per million requests
- Storage: $0.25 per GB-month

### S3 Pricing

**Standard Storage**:

- Storage: $0.023 per GB-month
- PUT requests: $0.005 per 1000 requests
- GET requests: $0.0004 per 1000 requests

### Lambda Pricing

**Compute**:

- $0.20 per 1M requests
- $0.0000166667 per GB-second

**Typical Campaign Generation**:

- 4 Lambda invocations × 128 MB × 5 seconds = ~$0.0001
- Total cost: ~$0.01-0.02 per campaign

## Future Enhancements

### Data Flow Improvements

1. **Implement GSI on DynamoDB**:

   - Query by user_id
   - Query by timestamp range

2. **Add Caching Layer**:

   - ElastiCache for frequently accessed campaigns
   - Reduce DynamoDB reads by 70%

3. **Implement Event Bridge**:

   - Decouple Lambda invocations
   - Enable event-driven architecture

4. **Add Step Functions**:

   - Replace sequential Lambda calls
   - Better error handling and retries
   - Visual workflow management

5. **Implement API Caching**:

   - Cache campaign results
   - Reduce Lambda invocations

6. **Add Data Lake**:
   - Stream DynamoDB changes to S3
   - Enable analytics and ML training
