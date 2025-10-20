# Image Generation Workflow

## Overview

The image generation system uses **asynchronous processing** via SQS to handle AI image generation requests using Amazon Bedrock Nova Canvas.

## Workflow Diagram

```
Client Request
     ↓
API Gateway (POST /api/assets/)
     ↓
SQS Integration (SendMessage)
     ↓
degenerals-mi-dev-image-generation-queue
     ↓
Generate Images Lambda (Event Source Mapping)
     ↓
Amazon Bedrock Nova Canvas
     ↓
┌─────────────────────────────────────┐
│  Store Image in S3                  │
│  Store Metadata in DynamoDB         │
└─────────────────────────────────────┘
     ↓
Client Polls Status (GET /api/assets/{request_id})
     ↓
Image Generation Status Lambda
     ↓
Return Status + S3 URL
```

## Detailed Flow

### Step 1: Submit Image Generation Request

**Endpoint**: `POST /api/assets/`

**Request Body**:

```json
{
  "prompt": "A futuristic cityscape at sunset",
  "style": "vivid",
  "aspect_ratio": "16:9",
  "user_id": "user123",
  "request_id": "req-456"
}
```

**Field Descriptions**:

- `prompt` (required): Text description of image to generate (10-1000 chars)
- `style` (optional): Style preset - `natural`, `vivid`, `anime`, `photographic`
  - Default: `natural`
- `aspect_ratio` (optional): Image dimensions - `1:1`, `16:9`, `9:16`, `4:3`, `3:4`
  - Default: `1:1`
- `user_id` (optional): User identifier for tracking
  - Default: `anonymous`
- `request_id` (optional): Unique request ID
  - Default: Auto-generated UUID

**Response** (HTTP 200):

```json
{
  "message": "Image generation request queued",
  "request_id": "req-456"
}
```

### Step 2: API Gateway → SQS Integration

API Gateway directly integrates with SQS using AWS service integration:

**Integration Type**: `AWS_PROXY` with SQS
**Queue URL**: `https://sqs.eu-west-1.amazonaws.com/584102815888/degenerals-mi-dev-image-generation-queue`
**Message Body**: `$request.body`

**IAM Role**: `apigateway-sqs-invoke-role`
**Policy**:

```json
{
  "Effect": "Allow",
  "Action": "sqs:SendMessage",
  "Resource": "arn:aws:sqs:eu-west-1:584102815888:degenerals-mi-dev-image-generation-queue"
}
```

### Step 3: SQS Queue Processing

**Queue Configuration**:

- **Visibility Timeout**: 300 seconds (5 minutes)
- **Message Retention**: 4 days
- **Receive Wait Time**: 0 seconds
- **Maximum Receives**: 3 (before DLQ)

**SQS Message Format**:

```json
{
  "Records": [
    {
      "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
      "body": "{\"prompt\": \"A futuristic cityscape at sunset\", \"style\": \"vivid\", \"aspect_ratio\": \"16:9\", \"user_id\": \"user123\", \"request_id\": \"req-456\"}",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:eu-west-1:584102815888:degenerals-mi-dev-image-generation-queue"
    }
  ]
}
```

### Step 4: Lambda Function Processing

**Function**: `generate-images-lambda`
**Trigger**: SQS Event Source Mapping
**Batch Size**: 1 message at a time
**Timeout**: 5 minutes

#### 4.1 Parse SQS Message

```python
for record in event.get('Records', []):
    message_body = json.loads(record['body'])
    prompt = message_body.get('prompt')
    style = message_body.get('style', 'natural')
    aspect_ratio = message_body.get('aspect_ratio', '1:1')
    user_id = message_body.get('user_id', 'anonymous')
    request_id = message_body.get('request_id', str(uuid.uuid4()))
```

#### 4.2 Store Initial Status in DynamoDB

```python
table.put_item(
    Item={
        'request_id': request_id,
        'user_id': user_id,
        'prompt': prompt,
        'style': style,
        'aspect_ratio': aspect_ratio,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
)
```

#### 4.3 Generate Image with Nova Canvas

**Model**: `amazon.nova-canvas-v1:0`

**Request Configuration**:

```python
image_generation_config = {
    'numberOfImages': 1,
    'quality': 'standard',
    'width': 1024 if aspect_ratio == '1:1' else 1280,
    'height': 1024 if aspect_ratio == '1:1' else 720,  # 16:9
    'cfgScale': 7.0  # Guidance scale
}

# Style-specific adjustments
if style == 'vivid':
    image_generation_config['cfgScale'] = 8.0
elif style == 'natural':
    image_generation_config['cfgScale'] = 6.0

request_body = {
    'taskType': 'TEXT_IMAGE',
    'textToImageParams': {
        'text': prompt,
        'negativeText': 'blurry, low quality, distorted, ugly'
    },
    'imageGenerationConfig': image_generation_config
}
```

**Bedrock Invocation**:

```python
response = bedrock_client.invoke_model(
    modelId='amazon.nova-canvas-v1:0',
    contentType='application/json',
    accept='application/json',
    body=json.dumps(request_body)
)
```

**Response Processing**:

```python
response_body = json.loads(response['body'].read())
image_data_base64 = response_body['images'][0]
image_data = base64.b64decode(image_data_base64)
```

#### 4.4 Store Image in S3

**Bucket**: `degenerals-mi-dev-generated-assets`
**Key Format**: `generated/{user_id}/{timestamp}_{request_id}_{sanitized_prompt}.png`

```python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
sanitized_prompt = prompt[:50].replace(' ', '_')
s3_key = f"generated/{user_id}/{timestamp}_{request_id}_{sanitized_prompt}.png"

s3_client.put_object(
    Bucket='degenerals-mi-dev-generated-assets',
    Key=s3_key,
    Body=image_data,
    ContentType='image/png'
)
```

**S3 URL**:

```
https://degenerals-mi-dev-generated-assets.s3.amazonaws.com/{s3_key}
```

#### 4.5 Update DynamoDB with Results

```python
bucket_name = 'degenerals-mi-dev-generated-assets'
s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

table.put_item(
    Item={
        'request_id': request_id,
        'user_id': user_id,
        'prompt': prompt,
        's3_key': s3_key,
        's3_url': s3_url,
        'style': style,
        'aspect_ratio': aspect_ratio,
        'generated_at': datetime.now().isoformat(),
        'status': 'completed'
    }
)
```

#### 4.6 Error Handling

**On Bedrock Error**:

```python
table.update_item(
    Key={'request_id': request_id},
    UpdateExpression='SET #status = :failed, error = :error',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':failed': 'failed',
        ':error': str(error)
    }
)
```

**On S3 Error**:

- Image generated but not stored
- Status remains `pending`
- Retry mechanism via SQS (up to 3 attempts)

### Step 5: Check Image Generation Status

**Endpoint**: `GET /api/assets/{request_id}`

**Example**: `GET /api/assets/req-456`

**Lambda**: `image-generation-status-lambda`

**DynamoDB Query**:

```python
response = table.get_item(Key={'request_id': request_id})
item = response.get('Item', {})
```

**Response - Pending** (HTTP 200):

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

**Response - Completed** (HTTP 200):

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

**Response - Failed** (HTTP 200):

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

**Response - Not Found** (HTTP 404):

```json
{
  "error": "Request not found",
  "request_id": "req-456"
}
```

## Environment Variables

### generate-images-lambda

- `S3_BUCKET_NAME`: `degenerals-mi-dev-generated-assets`
- `DYNAMODB_TABLE_NAME`: `generated_images`

### image-generation-status-lambda

- `DYNAMODB_TABLE_NAME`: `generated_images`

## IAM Permissions

### generate-images-lambda Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::degenerals-mi-dev-generated-assets/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem", "dynamodb:UpdateItem"],
      "Resource": "arn:aws:dynamodb:eu-west-1:584102815888:table/generated_images"
    },
    {
      "Effect": "Allow",
      "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage"],
      "Resource": "arn:aws:sqs:eu-west-1:584102815888:degenerals-mi-dev-image-generation-queue"
    }
  ]
}
```

## Performance Metrics

- **Average Generation Time**: 3-5 seconds
- **Image Size**: ~1-2 MB
- **Queue Processing**: <1 second
- **Total E2E Latency**: 5-10 seconds

## Best Practices

1. **Polling Strategy**: Poll every 2-3 seconds, max 10 times
2. **Timeout Handling**: Consider failed if >60 seconds
3. **Request ID**: Always generate and store client-side
4. **Error Recovery**: Check error field for troubleshooting
5. **S3 Access**: Images are publicly readable via HTTPS

## Troubleshooting

### Common Issues

**Issue**: "Internal Server Error" from API Gateway

- **Cause**: IAM role misconfiguration
- **Fix**: Verify `apigateway-sqs-invoke-role` has `sqs:SendMessage`

**Issue**: Status stuck at "pending"

- **Cause**: Lambda execution error
- **Fix**: Check CloudWatch logs for `generate-images-lambda`

**Issue**: "Malformed input request" from Bedrock

- **Cause**: Invalid `seed` or missing required fields
- **Fix**: Ensure `seed` is omitted or numeric, not `null`

**Issue**: "AccessDenied" S3 error

- **Cause**: S3 bucket policy missing `/*` wildcard
- **Fix**: Update resource to `arn:aws:s3:::bucket-name/*`
