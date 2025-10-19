# Architecture Overview

## System Architecture

The Degenerals Marketing Intelligence Platform is built on AWS serverless architecture with a two-tier failure handling system.

### High-Level Architecture

```
Client → API Gateway → Lambda Functions → Bedrock/External APIs
                              ↓
                         DynamoDB/S3
```

## Components

### 1. API Gateway
- **Type**: HTTP API (API Gateway v2)
- **Base URL**: `https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev`
- **Endpoints**:
  - `POST /api/campaign/tier-1` - Campaign generation
  - `POST /api/assets/` - Image generation (async)
  - `GET /api/assets/{request_id}` - Image status check
  - `POST /api/upload/presigned-url` - S3 upload URL
  - `GET /api/upload/status/{upload_id}` - Upload status

### 2. Lambda Functions

#### a. Intent Parser (`intent-parser-lambda`)
- **Purpose**: Orchestrates campaign generation workflow
- **Memory**: 128 MB
- **Timeout**: 5 minutes
- **Environment Variables**:
  - `BEDROCK_AGENT_ID`
  - `BEDROCK_AGENT_ALIAS_ID`
  - `YOUTUBE_API_KEY`

#### b. Image Analysis (`image-analysis-lambda`)
- **Purpose**: Analyzes product images using AWS Rekognition
- **Integrations**: Rekognition, DynamoDB, S3

#### c. Data Enrichment (`data-enrichment-lambda`)
- **Purpose**: Enriches product data with YouTube trends
- **External APIs**: YouTube Data API v3

#### d. Cultural Intelligence (`cultural-intelligence-lambda`)
- **Purpose**: Provides market-specific cultural insights
- **AI Model**: Amazon Bedrock (Claude/Nova)

#### e. Generate Images (`generate-images-lambda`)
- **Purpose**: Generates images using Amazon Nova Canvas
- **Trigger**: SQS queue
- **Memory**: 128 MB
- **Environment Variables**:
  - `S3_BUCKET_NAME`: `degenerals-mi-dev-generated-assets`
  - `DYNAMODB_TABLE_NAME`: `generated_images`

#### f. Image Generation Status (`image-generation-status-lambda`)
- **Purpose**: Returns status of image generation requests
- **Environment Variables**:
  - `DYNAMODB_TABLE_NAME`: `generated_images`

### 3. Data Storage

#### DynamoDB Tables
1. **products**
   - Partition Key: `product_id`
   - Stores: Product metadata, analysis results, enrichment data

2. **generated_images**
   - Partition Key: `request_id`
   - Stores: Image generation metadata, S3 URLs, status

#### S3 Buckets
1. **degenerals-mi-dev-images**
   - Purpose: Product image uploads
   - Access: Private with presigned URLs

2. **degenerals-mi-dev-generated-assets**
   - Purpose: AI-generated marketing assets
   - Access: Public read for generated images

### 4. Message Queues

#### SQS Queue: `degenerals-mi-dev-image-generation-queue`
- **Purpose**: Decouple image generation requests
- **Consumers**: `generate-images-lambda`
- **Dead Letter Queue**: Configured for failed messages

### 5. AI/ML Services

#### Amazon Bedrock
1. **Nova Pro** (`arn:aws:bedrock:eu-west-1::inference-profile/eu.amazon.nova-pro-v1:0`)
   - Campaign synthesis
   - Market analysis
   - Content generation

2. **Nova Canvas** (`amazon.nova-canvas-v1:0`)
   - Image generation
   - Visual asset creation

#### AWS Rekognition
- Image labeling
- Object detection
- Scene analysis

## Network Architecture

### VPC Configuration
- **Region**: eu-west-1 (Ireland)
- **Account**: 584102815888

### IAM Roles and Policies

- **Role**: `apigateway-sqs-invoke-role`
- **Permissions**: `sqs:SendMessage`

#### Lambda Execution Roles
Each Lambda has specific IAM roles with least-privilege access:
- Bedrock model invocation
- DynamoDB read/write
- S3 read/write
- CloudWatch Logs
- SQS receive/delete messages

## Security

### Authentication & Authorization
- API Gateway: Currently open (add API keys for production)
- S3: Bucket policies for public/private access
- Lambda: IAM role-based access

### Data Encryption
- **At Rest**: S3 server-side encryption, DynamoDB encryption
- **In Transit**: HTTPS/TLS for all API calls

## Monitoring & Logging

### CloudWatch
- Lambda function logs: `/aws/lambda/{function-name}`
- API Gateway logs: Access logs enabled
- Metrics: Invocation counts, errors, duration