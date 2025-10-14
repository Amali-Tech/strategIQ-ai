# AWS AI Hackathon - YouTube Enriched Marketing Campaign Generator

{toc}

## Overview

This project demonstrates an AI-driven marketing campaign generation system using AWS serverless services, YouTube Data API, and Amazon Bedrock. The solution automatically analyzes product images, enriches them with YouTube trend data, and generates targeted marketing campaigns using generative AI.

{info}
**Project Goal**: Create an automated pipeline that transforms product images into comprehensive marketing campaigns by leveraging computer vision, social media trends, and generative AI.
{info}

---

## System Architecture

This solution implements a **two-phase serverless architecture** with event-driven processing:

### Phase 1: Image Upload and Analysis

{color:#0747a6}**Initial Processing Pipeline**{color}

1. **Web Application** uploads product images and metadata to Amazon S3
2. **S3 Event Trigger** automatically invokes AWS Lambda for immediate processing
3. **Amazon Rekognition** analyzes images for:
   - Product attributes and categories
   - Text detection (OCR)
   - Content moderation
   - Visual elements identification
4. **Analysis Results** stored in DynamoDB Table 1 with unique image hash for tracking
5. **Pipeline Status** updated for frontend monitoring

### Phase 2: Enrichment and Campaign Generation

{color:#0747a6}**AI-Powered Enhancement Pipeline**{color}

1. **DynamoDB Stream** captures changes from Table 1
2. **EventBridge Pipes** orchestrates the enrichment workflow:
   - Filters completed analysis records
   - Routes events to enrichment processing
   - Manages error handling and retries
3. **Enrichment Lambda** performs YouTube trend analysis:
   - Builds intelligent search queries from product data
   - Fetches trending videos via YouTube Data API v3
   - Analyzes social media engagement metrics
4. **Enriched Data** stored in DynamoDB Table 2
5. **Campaign Generator Lambda** creates marketing content:
   - Uses Amazon Bedrock (Nova Pro models)
   - Generates comprehensive campaign strategies
   - Incorporates trend analysis and product insights
6. **Final Results** stored with campaign recommendations

{note}
**Event-Driven Design**: The entire pipeline is event-driven, ensuring automatic processing without manual intervention and providing resilience through managed retry mechanisms.
{note}

---

## Key Components

### EventBridge Pipes

{color:#6554c0}**Serverless Integration Hub**{color}

The EventBridge Pipe serves as the backbone of our processing pipeline:

- **Source**: DynamoDB Table 1 stream
- **Filtering**: Processes only completed analysis records
- **Transformation**: Optimizes data format for downstream processing
- **Target**: Enrichment and Campaign Generation Lambdas
- **Error Handling**: Built-in retry logic and dead letter queues

### Enrichment Lambda Function

{color:#6554c0}**YouTube Trend Analysis Engine**{color}

**File**: `enrichment_lambda.py`

**Key Responsibilities**:

- Receives DynamoDB stream events via EventBridge Pipes
- Extracts product attributes and visual analysis data
- Constructs optimized YouTube search queries based on:
  - Product categories (footwear, clothing, electronics, etc.)
  - Visual attributes (colors, materials, style)
  - Market positioning keywords
- Fetches trending videos using YouTube Data API v3
- Analyzes engagement metrics (views, likes, comments)
- Stores enriched data for campaign generation

**Advanced Features**:

- Intelligent query building with confidence-based attribute weighting
- Market segment-specific search optimization
- Comprehensive error handling and logging
- Support for multiple event formats (EventBridge, DynamoDB streams)

### Campaign Generator Lambda

{color:#6554c0}**AI-Powered Marketing Engine**{color}

**File**: `campaign_generator_lambda.py`

**Key Responsibilities**:

- Processes enriched events from EventBridge Pipes
- Retrieves complete product and trend data from DynamoDB
- Constructs detailed prompts for AI models including:
  - Product specifications and visual analysis
  - YouTube trend insights and engagement data
  - Target audience demographics
  - Marketing best practices
- Leverages Amazon Bedrock models for campaign generation
- Stores comprehensive marketing recommendations

**AI Integration**:

- Uses Amazon Nova Pro models via Amazon Bedrock
- Context-aware prompt engineering
- Multi-format output generation (social media, email, web)
- Brand voice adaptation and tone optimization

---

## Technology Stack

### AWS Services

- **Amazon S3**: Image storage and static website hosting
- **AWS Lambda**: Serverless compute for all processing functions
- **Amazon DynamoDB**: NoSQL database for analysis and campaign data
- **Amazon Rekognition**: Computer vision and image analysis
- **Amazon Bedrock**: Generative AI model access
- **EventBridge Pipes**: Event-driven orchestration
- **API Gateway**: REST API endpoints for frontend integration
- **CloudFormation/Terraform**: Infrastructure as Code

### External APIs

- **YouTube Data API v3**: Trend analysis and video metadata
- **OAuth 2.0**: Secure API authentication

### Development Tools

- **Python 3.11**: Runtime environment
- **boto3**: AWS SDK for Python
- **Terraform**: Infrastructure provisioning
- **Make**: Build automation

---

## Deployment Guide

### Prerequisites

{warning}
**Required Setup**:

- AWS Account with appropriate IAM permissions
- YouTube Data API v3 key ([Get API Key](https://developers.google.com/youtube/v3/getting-started))
- Amazon Bedrock model access (Amazon Nova Pro recommended)
- Terraform installed locally
  {warning}

### Environment Configuration

1. **Clone the repository**:

```bash
git clone https://github.com/Amali-Tech/degenerals-infra.git
cd degenerals-infra
```

2. **Configure environment variables**:

```bash
# Create environment file
cp terraform/setup.env.example terraform/setup.env

# Edit with your values
export YOUTUBE_API_KEY=your_youtube_api_key_here
export AWS_REGION=eu-west-1
export PROJECT_NAME=aws-ai-hackathon
export ENVIRONMENT=dev
```

3. **Set up Terraform backend**:

```bash
# Configure S3 backend for state management
cp terraform/terraform.tfbackend.example terraform/terraform.tfbackend
# Edit with your S3 bucket and DynamoDB table for state locking
```

### Infrastructure Deployment

{code:language=bash}

# Initialize Terraform

cd terraform
terraform init

# Review planned changes

terraform plan

# Deploy infrastructure

terraform apply

# Note the output endpoints for frontend integration

{code}

### Verification Steps

1. **Check S3 bucket creation**:

   - Verify bucket exists with proper CORS configuration
   - Test presigned URL generation

2. **Validate Lambda functions**:

   - Confirm all functions are deployed with correct IAM roles
   - Test individual functions with sample events

3. **Test EventBridge Pipes**:
   - Upload a test image to trigger the pipeline
   - Monitor CloudWatch logs for processing status

---

## Testing & Monitoring

### Testing the Pipeline

{tip}
**Quick Test**: Upload an image via the presigned URL endpoint to trigger the complete pipeline
{tip}

1. **Generate Upload URL**:

```bash
curl -X POST "https://your-api-gateway-url/dev/presigned-url" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test-product.jpg", "filetype": "image/jpeg"}'
```

2. **Upload Image**:

```bash
curl -X PUT "presigned-url-from-step-1" \
  -H "Content-Type: image/jpeg" \
  --data-binary @test-product.jpg
```

3. **Monitor Progress**:
   - Check DynamoDB Table 1 for analysis results
   - Verify enriched data in DynamoDB Table 2
   - Review generated campaigns

### Monitoring & Observability

**CloudWatch Dashboards**:

- Lambda function metrics (invocations, errors, duration)
- DynamoDB read/write capacity and throttling
- EventBridge Pipes processing metrics

**Logging Strategy**:

- Structured JSON logs for easy parsing
- Request tracking with correlation IDs
- Error categorization and alerting

**Key Metrics to Monitor**:

- End-to-end pipeline latency
- YouTube API quota usage
- Bedrock model invocation costs
- Error rates by component

---

## API Endpoints

### 🌐 REST API Reference

| Endpoint              | Method | Description             | Authentication |
| --------------------- | ------ | ----------------------- | -------------- |
| `/presigned-url`      | POST   | Generate S3 upload URL  | API Key        |
| `/status/{imageHash}` | GET    | Check processing status | API Key        |

**Example Responses**:

{code:language=json}
// POST /presigned-url
{
"uploadUrl": "https://bucket.s3.region.amazonaws.com/...",
"imageHash": "unique-hash-identifier"
}

// GET /status/{imageHash}
{
"status": "completed",
"pipeline_stage": "campaign_generated",
"results": {
"analysis": {...},
"enrichment": {...},
"campaigns": {...}
}
}
{code}

---

## Cost Optimization

### Cost Breakdown

**Primary Cost Drivers**:

- Amazon Bedrock model invocations (~$0.10-0.50 per campaign)
- YouTube API calls (free tier: 10,000 units/day)
- Lambda invocations and compute time
- DynamoDB read/write operations
- S3 storage and transfer

**Optimization Strategies**:

- Use DynamoDB on-demand pricing for variable workloads
- Implement intelligent caching for YouTube API responses
- Optimize Lambda memory allocation based on actual usage
- Configure S3 lifecycle policies for old images

---

## Troubleshooting

### Common Issues

{expand:Common Issues}

**Issue**: "Unexpected event format" in enrichment Lambda
**Solution**: EventBridge Pipes sends events as arrays. Ensure the Lambda handles `isinstance(event, list)` format.

**Issue**: YouTube API quota exceeded
**Solution**: Implement exponential backoff and request caching. Consider upgrading to paid tier.

**Issue**: Bedrock access denied
**Solution**: Verify model access is enabled in the correct AWS region and IAM permissions are configured.

**Issue**: Lambda timeout on large images
**Solution**: Increase Lambda timeout and memory, or implement asynchronous processing.

{expand}

### Debug Mode

Enable detailed logging by setting environment variable:

```bash
export DEBUG_MODE=true
```

---

## Security Considerations

### Security Best Practices

**Data Protection**:

- Images are automatically deleted after processing (configurable retention)
- API keys are stored in AWS Secrets Manager
- All data in transit is encrypted (HTTPS/TLS)
- DynamoDB encryption at rest enabled

**Access Control**:

- IAM roles follow principle of least privilege
- API Gateway with API key authentication
- VPC endpoints for internal service communication
- Resource-based policies for cross-service access

**Compliance**:

- GDPR-compliant data handling
- Audit logging for all operations
- Data residency controls via AWS region selection

---

## Performance Metrics

### Expected Performance

| Metric                | Value         | Notes                                 |
| --------------------- | ------------- | ------------------------------------- |
| Image Analysis        | 5-15 seconds  | Depends on image size and complexity  |
| YouTube Enrichment    | 2-5 seconds   | Limited by API response time          |
| Campaign Generation   | 10-30 seconds | Varies by model and prompt complexity |
| End-to-End Processing | 20-60 seconds | Total pipeline completion time        |

### Scalability

**Concurrent Processing**:

- Lambda: 1000 concurrent executions (default limit)
- DynamoDB: Auto-scaling based on traffic
- EventBridge Pipes: Handles up to 10,000 events/second

**Throughput Optimization**:

- Batch processing for multiple images
- Parallel YouTube API calls
- Asynchronous campaign generation

---

## Future Enhancements

### Roadmap

**Phase 3 - Advanced Analytics**:

- Real-time campaign performance tracking
- A/B testing framework for generated content
- Machine learning model for campaign effectiveness prediction

**Phase 4 - Multi-Platform Integration**:

- Instagram and TikTok trend analysis
- Cross-platform campaign optimization
- Automated social media posting

**Phase 5 - Enterprise Features**:

- Multi-tenant architecture
- Advanced user management
- Custom AI model fine-tuning

---

## Contributing

### Development Guidelines

**Code Standards**:

- Follow PEP 8 for Python code
- Use type hints for better code documentation
- Implement comprehensive error handling
- Write unit tests for all Lambda functions

**Infrastructure Changes**:

- All changes must be made via Terraform
- Test in development environment first
- Document breaking changes in migration guides

---

## Support & Resources

### Additional Resources

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- [EventBridge Pipes Documentation](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html)

### Getting Help

**Internal Support**:

- Slack: #ai-hackathon-support
- Email: christian.solomon@amalitech.com

**Community Resources**:

- GitHub Issues for bug reports
- AWS Support for infrastructure issues
- Stack Overflow for development questions

---

{panel:title=Project Information|borderStyle=dashed|borderColor=#ccc|titleBGColor=#f4f5f7|bgColor=#fff}
**Project**: AWS AI Hackathon - Marketing Campaign Generator  
**Team**: AI Innovation Team  
**Last Updated**: September 30, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
{panel}
