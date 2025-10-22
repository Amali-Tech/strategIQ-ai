# StrategIQ Marketing Campaign Generator

> **AI-driven, serverless pipeline that converts product images into fully enriched, trend-informed marketing campaigns using AWS, YouTube Data API, and Amazon Bedrock.**

[![Terraform](https://img.shields.io/badge/Terraform-1.5+-7B42BC?style=for-the-badge&logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![EventBridge](https://img.shields.io/badge/AWS-EventBridge-DD344C?style=for-the-badge&logo=amazon-aws)](https://docs.aws.amazon.com/eventbridge/)
[![YouTube API](https://img.shields.io/badge/YouTube-Data%20API-red?style=for-the-badge&logo=youtube)](https://developers.google.com/youtube/v3)
[![Amazon Bedrock](https://img.shields.io/badge/Amazon-Bedrock-232F3E?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/)

---

## Project Overview

This project implements an automated, event-driven marketing campaign generation system. It ingests product images, extracts rich visual and contextual attributes, enriches them with real-time Social Media trend intelligence, and generates multi-channel marketing campaign assets using generative AI models hosted on Amazon Bedrock.

**Core Value Proposition**:

- Eliminate manual research steps
- Accelerate creative generation
- Leverage current audience engagement signals
- Produce consistent, data-backed campaign strategies

---

## System Architecture

A two-phase, fully serverless architecture orchestrated via Amazon EventBridge Pipes:

![Architecture (add diagram)](documentation/architecture-diagrams/images/hackathon-solution-architecture.jpg)

### Processing Flow

**Primary Flow (Bedrock Agent Orchestration)**:

1. User uploads image + campaign requirements via API Gateway
2. **Intent Parser Lambda** invokes **Amazon Bedrock Agent** with campaign context
3. Agent autonomously calls action groups as needed:
   - **Image Analysis** → Rekognition labels + visual insights
   - **Data Enrichment** → YouTube trends + engagement metrics
   - **Cultural Intelligence** → Market-specific adaptation guidelines
4. Agent synthesizes all gathered data into comprehensive campaign JSON
5. Campaign artifacts stored in DynamoDB and S3
6. API returns complete campaign strategy

### Technology Stack

| Component              | Technology / Service                           | Docs / Section                              |
| ---------------------- | ---------------------------------------------- | ------------------------------------------- |
| AI Orchestration       | **Amazon Bedrock Agent** with Action Groups    | [Bedrock Agent](#amazon-bedrock-agent)      |
| Image Analysis         | AWS Lambda (Python 3.11) + Amazon Rekognition  | [Image Analysis](#image-analysis)           |
| Trend Enrichment       | AWS Lambda + YouTube Data API v3               | [Trend Enrichment](#trend-enrichment)       |
| Campaign Generation    | AWS Lambda + Amazon Bedrock (Nova / Claude)    | [Campaign Generation](#campaign-generation) |
| Cultural Intelligence  | AWS Lambda + Amazon Bedrock + Knowledge Bases  | [Campaign Generation](#campaign-generation) |
| Orchestration          | EventBridge Pipes + DynamoDB Streams           | [Event Orchestration](#event-orchestration) |
| Data Storage           | Amazon DynamoDB (2 tables) + S3 object storage | [Data Model](#data-model)                   |
| API Layer              | Amazon API Gateway (REST)                      | [API Reference](#api-reference)             |
| Infrastructure as Code | Terraform                                      | [Infrastructure](#infrastructureterraform)  |
| Observability          | CloudWatch Logs / Metrics / Dashboards         | [Monitoring](#monitoring--operations)       |

### Quick Start Navigation

Choose where you want to contribute or explore:

- [Amazon Bedrock Agent (AI Orchestration)](#amazon-bedrock-agent)
- [Image Analysis Pipeline](#image-analysis)
- [Trend Enrichment Service](#trend-enrichment)
- [Campaign Generation (AI)](#campaign-generation)
- [Infrastructure / Terraform](#infrastructureterraform)
- [Testing & Monitoring](#testing--monitoring)

---

## Image Analysis

### Overview

Performs initial extraction of visual and contextual product attributes using Amazon Rekognition (labels, moderation, text) and computes a deterministic image hash for correlation.

### Responsibilities

- Label + category inference
- Text/OCR extraction (if present)
- Content safety / moderation flags
- Attribute confidence scoring
- Status persistence to DynamoDB (Analysis Table)

### Trigger & Event Shape

- Source: S3 ObjectCreated event
- Output: Normalized record written to DynamoDB with fields: `image_hash`, `labels[]`, `text[]`, `moderation_flags[]`, `categories[]`, `status`.

### Key File(s)

- `scripts/analyse_image_lambda.py` (or Lambda source directory if refactored into `lambda/` subfolder)

### Potential Enhancements

- Multi-language text normalization
- Embeddings generation for semantic clustering
- Duplicate detection via perceptual hashing

---

## Amazon Bedrock Agent

### Overview

The system leverages Amazon Bedrock Agents as the intelligent orchestration layer for campaign generation. The agent coordinates multiple specialized action groups, makes autonomous decisions about data gathering, and synthesizes comprehensive marketing campaigns.

### Agent Architecture

#### Core Configuration

- **Agent Type**: Amazon Bedrock Agent with Action Groups
- **Primary Model**: Amazon Nova or Claude (configurable)
- **Session Management**: Correlation-based session IDs for request tracking
- **Instruction Set**: Custom prompt engineering for marketing campaign generation
- **Deployment**: Managed through Terraform with versioned aliases

#### Action Groups (Tool Calling)

The Bedrock Agent has three specialized action groups, each backed by a Lambda function with dual invocation support:

**1. Image Analysis Action Group** (`image-analysis`)

- **Endpoint**: `/analyze-product-image`
- **Backend**: `image-analysis-lambda`
- **Function**: Analyzes product visuals using Amazon Rekognition
- **Input Parameters**:
  - `product_info` (object): Product name, description, category
  - `s3_info` (object): S3 bucket and key for image location
- **Returns**: Product ID, detected labels, visual attributes, marketing insights
- **Schema**: OpenAPI 3.0 specification in `lambda-handlers/image_analysis/openapi_schema.json`

**2. Data Enrichment Action Group** (`data-enrichment`)

- **Endpoint**: `/enrich-campaign-data`
- **Backend**: `data-enrichment-lambda`
- **Function**: Enriches campaigns with real-time market intelligence
- **Input Parameters**:
  - `product_id` (string): Product identifier
  - `search_query` (string): Keywords for trend search
  - `max_results` (integer): Limit for search results
  - `content_type` (string): Type of content to search
- **Returns**: YouTube trends, engagement metrics, content recommendations
- **External APIs**: YouTube Data API v3
- **Schema**: OpenAPI 3.0 specification in `lambda-handlers/data_enrichment/openapi_schema.json`

**3. Cultural Intelligence Action Group** (`cultural-intelligence`)

- **Endpoint**: `/analyze-cultural-insights`
- **Backend**: `cultural-intelligence-lambda`
- **Function**: Provides market-specific cultural adaptation
- **Input Parameters**:
  - `product_id` (string): Product identifier
  - `target_markets` (object): List of target markets/regions
  - `campaign_type` (string): Type of campaign (social_media, etc.)
  - `product_category` (string): Product category
- **Returns**: Cultural insights, communication guidelines, market-specific recommendations
- **AI Model**: Amazon Bedrock (Claude/Nova) for insight generation
- **Knowledge Base**: Structured cultural data in `knowledge-bases/` directory
- **Schema**: OpenAPI 3.0 specification in `lambda-handlers/cultural_intelligence/openapi_schema.json`

### Agent Behavior & Strategy

#### Intelligent Tool Selection

The agent autonomously decides:

- Which action groups to invoke based on available input data
- Order of invocation for optimal data dependency resolution
- Whether to proceed with partial data if an action group fails

#### Resilience Principles

1. **Single-Call Policy**: Each action group invoked at most once (no automatic retries)
2. **Graceful Degradation**: Generates campaigns even with partial data availability
3. **Aggressive Inference**: Uses foundation model knowledge to fill gaps
4. **Always Returns Valid JSON**: Guarantees schema-compliant output regardless of failures

### Integration Pattern

```python
# Agent invocation from intent-parser-lambda
response = bedrock_agent_runtime.invoke_agent(
    agentId=BEDROCK_AGENT_ID,
    agentAliasId=BEDROCK_AGENT_ALIAS_ID,
    sessionId=f"session-{correlation_id}",
    inputText=prompt_with_context
)
```

Each action group Lambda implements:

```python
def lambda_handler(event, context):
    # Detect invocation source
    if 'messageVersion' in event and 'requestBody' in event:
        # Bedrock Agent format
        return handle_bedrock_agent_invocation(event, context)
    else:
        # Direct invocation format
        return handle_direct_invocation(event, context)
```

### Environment Variables

- `BEDROCK_AGENT_ID`: Unique identifier for the Bedrock Agent
- `BEDROCK_AGENT_ALIAS_ID`: Agent version alias (e.g., DRAFT, PROD)

### Monitoring & Observability

- **CloudWatch Logs**: Agent invocations, tool calls, response streams
- **Correlation IDs**: End-to-end request tracking across action groups
- **Performance Metrics**: Tool call latency, success rates, response times

### Key Files

- **Agent Instructions**: `documentation/bedrock-agent-instrcution.md`
- **Workflow Documentation**: `documentation/campaign-generation.docs.md`
- **Terraform Configuration**: `terraform/variables.tf` (agent ID/alias)

### Benefits

- **Autonomous Decision Making**: Agent determines optimal data gathering strategy
- **Natural Language Understanding**: Interprets user intent and campaign objectives
- **Context Preservation**: Maintains conversation state across multi-turn interactions
- **Extensible**: New action groups can be added without core logic changes
- **Cost Optimized**: Only invokes necessary tools based on available data

---

## Trend Enrichment

### Overview

Consumes filtered DynamoDB stream events (only completed analyses) via EventBridge Pipes and enriches records with live YouTube trend insights.

### Responsibilities

- Intelligent query construction from product attributes
- YouTube Data API v3 search + statistics retrieval
- Engagement signal extraction (views, likes, comments ratios)
- Topic + audience intent inference
- Writes enriched payload to Enrichment Table (DynamoDB)

### Key File(s)

- `scripts/enrichment_lambda.py`

### Advanced Features

- Confidence-weighted keyword ranking
- Query diversification to avoid quota inefficiencies
- Graceful degradation on partial API failures

---

## Campaign Generation

### Overview

Generates structured, multi-channel marketing deliverables using Amazon Bedrock Agents with specialized action groups for intelligent campaign orchestration.

### Orchestration Architecture

#### Bedrock Agent with Tool Calling

The system first attempts intelligent campaign generation using a Bedrock Agent (`intent-parser-lambda`) equipped with three specialized action groups:

**1. Image Analysis Action Group**

- **Lambda**: `image-analysis-lambda`
- **API Path**: `/analyze-product-image`
- **Purpose**: Analyzes product images using Amazon Rekognition
- **Capabilities**:
  - Label & object detection
  - Visual attribute extraction
  - Marketing insights generation
- **Output**: Updates DynamoDB with `analysis_status='image_analyzed'`
- **OpenAPI Schema**: `lambda-handlers/image_analysis/openapi_schema.json`

**2. Data Enrichment Action Group**

- **Lambda**: `data-enrichment-lambda`
- **API Path**: `/enrich-campaign-data`
- **Purpose**: Enriches campaigns with real-time market intelligence
- **Data Sources**:
  - YouTube Data API v3 (trending videos, engagement metrics)
  - Content performance insights
  - Competitive intelligence
- **Output**: Updates DynamoDB with `enrichment_status='data_enriched'`
- **OpenAPI Schema**: `lambda-handlers/data_enrichment/openapi_schema.json`

**3. Cultural Intelligence Action Group**

- **Lambda**: `cultural-intelligence-lambda`
- **API Path**: `/analyze-cultural-insights`
- **Purpose**: Provides market-specific cultural adaptation guidance
- **Capabilities**:
  - Cultural context analysis (colors, symbols, messaging)
  - Regional preference insights
  - Localization recommendations
  - Communication guidelines
- **AI Model**: Amazon Bedrock (Claude/Nova)
- **Output**: Updates DynamoDB with `cultural_status='culturally_enriched'`
- **OpenAPI Schema**: `lambda-handlers/cultural_intelligence/openapi_schema.json`

**Agent Configuration**:

- **Agent ID**: Environment variable `BEDROCK_AGENT_ID`
- **Alias ID**: Environment variable `BEDROCK_AGENT_ALIAS_ID`
- **Session Management**: Correlation-ID based sessions
- **Instruction Set**: `documentation/bedrock-agent-instrcution.md`

**Agent Behavior**:

- Graceful degradation on partial failures
- Aggressive inference from available data
- **Always** generates valid campaign JSON regardless of action group success

### Campaign Output Schema

The agent produces comprehensive campaign artifacts conforming to a strict JSON schema:

**Required Fields**:

- `product`: Description, image details, detected labels
- `content_ideas[]`: Platform-specific content (Instagram, TikTok, YouTube, LinkedIn, Twitter, Facebook)
  - Topic, engagement score, caption, hashtags
- `campaigns[]`: Multi-week campaign strategies
  - Name, duration, posting schedule, platform adaptations
  - Weekly calendar with activities
- `generated_assets`: Ready-to-use creative materials
  - Image generation prompts
  - Video scripts (short/long form)
  - Email templates
  - Blog outlines
- `related_youtube_videos[]`: Trending reference content
- `platform_recommendations`: Primary platforms with rationale
- `market_insights`: Cultural considerations, trending content types, audience preferences

### Key Files

- **Orchestrator**: `lambda-handlers/intent_parser/handler.py`
- **Action Groups**:
  - `lambda-handlers/image_analysis/handler.py`
  - `lambda-handlers/data_enrichment/handler.py`
  - `lambda-handlers/cultural_intelligence/handler.py`
- **Agent Instructions**: `documentation/bedrock-agent-instrcution.md`
- **Workflow Documentation**: `documentation/campaign-generation.docs.md`

### Advanced Features

**Sentiment Analysis Integration** (Optional)

- **Lambda**: `sentiment-analysis-lambda`
- **Purpose**: Competitor and market sentiment analysis
- **Capabilities**:
  - YouTube content sentiment analysis (AWS Comprehend)
  - Action item generation from sentiment data (Bedrock)
  - Comprehensive competitor intelligence
- **Invocation**: Triggered for `/optimize-campaign` endpoint
- **OpenAPI Schema**: `lambda-handlers/sentiment_analysis/openapi_schema.json`
- **Note**: Can be configured as 4th action group for Bedrock Agent

**System Features**

- **Correlation Tracking**: UUID-based request correlation across all components
- **Dual Invocation Support**: Each action group Lambda handles both Bedrock agent format and direct invocation
- **Error Resilience**: Structured error responses compatible with Bedrock agent protocol
- **Streaming Support**: Agent responses streamed back for real-time feedback

### Future Opportunities

- A/B variant generation with statistical confidence
- Multi-model ensemble for campaign quality scoring
- Real-time campaign performance feedback loops
- Fine-tuned domain models for vertical-specific campaigns

---

## Event Orchestration

### Core Pattern

DynamoDB Streams → EventBridge Pipe (filter + transform) → Target Lambda. This ensures minimal custom glue code and native retry / DLQ support.

### Benefits

- Fine-grained event filtering (only completed analysis states)
- Reduced Lambda cold start pressure
- Centralized error handling
- Natural backpressure through stream sequencing

---

## Data Model

| Table / Store         | Purpose                         | Key(s) / Indexes                          |
| --------------------- | ------------------------------- | ----------------------------------------- |
| Analysis Table        | Raw + processed visual analysis | PK: `image_hash`                          |
| Enrichment Table      | Trend + engagement metadata     | PK: `image_hash`                          |
| Campaign Output (opt) | Final campaign asset bundle     | PK: `image_hash` (or composite if needed) |
| S3 (images)           | Original product images         | Object key (namespaced by upload)         |

Optional secondary indexes can support querying by category or campaign status.

---

## Infrastructure/Terraform

### Overview

All AWS resources are provisioned using Terraform. Recommended layout leverages environment-specific workspaces / `tfvars` to isolate deployments.

### Core Resources

- **Amazon Bedrock Agent** (with 3 action groups configured)
- S3 bucket (image ingress + product images)
- DynamoDB tables (products + analysis data)
- Lambda functions:
  - Intent Parser (orchestrator)
  - Image Analysis (action group)
  - Data Enrichment (action group)
  - Cultural Intelligence (action group)
  - Image Generation (Nova Canvas)
  - Sentiment Analysis (optional)
- IAM roles with Bedrock Agent permissions
- API Gateway (REST endpoints)
- CloudWatch dashboards / alarms (optional)

### Prerequisites

- AWS Account & credentials (`aws configure`)
- Terraform ≥ 1.5
- Python 3.11 runtime for Lambdas
- YouTube Data API key (from Google Cloud Console)
- **Amazon Bedrock Agent** created with 3 action groups configured
- Amazon Bedrock model access approved in selected region (Nova/Claude)
- Bedrock Agent ID and Alias ID from AWS Console

### Environment Variables / Secrets

Add to Parameter Store / Secrets Manager or export prior to `terraform apply`:

```bash
export YOUTUBE_API_KEY=your_youtube_api_key
export AWS_REGION=eu-west-1
export PROJECT_NAME=strategiq-campaign-gen
export ENVIRONMENT=dev
export BEDROCK_AGENT_ID=your_bedrock_agent_id
export BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id
```

**Required for Bedrock Agent**:

- `BEDROCK_AGENT_ID`: Found in AWS Bedrock console after agent creation
- `BEDROCK_AGENT_ALIAS_ID`: Agent version alias (e.g., `YZRQ8FV4GH` for latest)

### Deployment Steps (Baseline)

```bash
git clone https://github.com/Amali-Tech/degenerals-infra.git
cd degenerals-infra/terraform
cp terraform.tfbackend.example terraform.tfbackend   # configure remote state
terraform init
terraform plan
terraform apply -auto-approve
```

Capture the output values for API endpoints and resource ARNs.

---

## API Reference

| Method | Endpoint              | Description               | Auth    |
| ------ | --------------------- | ------------------------- | ------- |
| POST   | `/presigned-url`      | Generate signed S3 upload | API Key |
| GET    | `/status/{imageHash}` | Retrieve pipeline status  | API Key |

### Example: Generate Upload URL

```bash
curl -X POST "$API_BASE/presigned-url" \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_KEY' \
  -d '{"filename":"test.jpg","filetype":"image/jpeg"}'
```

### Example: Poll Status

```bash
curl -H 'x-api-key: YOUR_KEY' "$API_BASE/status/<imageHash>"
```

### Sample Status Response

```json
{
  "status": "completed",
  "pipeline_stage": "campaign_generated",
  "results": {
    "analysis": { "labels": [] },
    "enrichment": { "trends": [] },
    "campaigns": { "strategy_summary": "..." }
  }
}
```

---

## Testing & Monitoring

### Quick End-to-End Test

1. Request presigned URL
2. Upload sample product image
3. Watch DynamoDB stream activity & Lambda logs
4. Query status endpoint until `campaign_generated`

### Key CloudWatch Metrics

- Lambda: Invocations / Errors / Duration / Throttles
- DynamoDB: RCUs / WCUs / ThrottledRequests
- EventBridge: Pipe delivery failures
- API Gateway: 4XX / 5XX error counts

### Logging Strategy

- Structured JSON logs with correlation id (image hash)
- Severity segmentation (INFO, WARN, ERROR)
- Retry + DLQ visibility via EventBridge metrics

---

## Performance Benchmarks (Typical)

| Stage               | Latency (avg) | Notes                               |
| ------------------- | ------------- | ----------------------------------- |
| Image Analysis      | 5–15s         | Dependent on Rekognition label set  |
| YouTube Enrichment  | 2–5s          | API latency + query diversification |
| Campaign Generation | 10–30s        | Model + prompt complexity           |
| End-to-End Pipeline | 20–60s        | Aggregate                           |

Optimization levers: batching queries, prompt token reduction, concurrency tuning.

---

## Security

### Core Controls

- IAM least-privilege roles per Lambda
- API Key (baseline) – recommend upgrade to Cognito/OAuth for production
- Encrypted at rest (S3 SSE, DynamoDB default encryption)
- TLS enforced via API Gateway & presigned URL policies
- Parameter Store / Secrets Manager for sensitive values

### Hardening Opportunities

- WAF in front of API Gateway
- Structured PII classification (if adding user data)
- Quota guards for external API usage

---

## Troubleshooting

| Symptom                              | Likely Cause                         | Action                                          |
| ------------------------------------ | ------------------------------------ | ----------------------------------------------- |
| Agent invocation fails               | Invalid Agent ID or Alias            | Verify environment variables match AWS Console  |
| Action group not being called        | OpenAPI schema mismatch              | Validate schema against agent configuration     |
| Agent returns empty response         | Model token limit exceeded           | Reduce prompt size or use larger model          |
| Missing enrichment data              | Filter rejected event                | Verify DynamoDB item status field               |
| YouTube quota exceeded               | Excessive search permutations        | Introduce caching / backoff                     |
| Bedrock access denied                | Region/model permissions not enabled | Enable model access in console                  |
| Lambda timeout (campaign generation) | Large prompt / slow model            | Increase timeout & optimize prompt              |
| Event not reaching enrichment Lambda | Pipe filter mismatch                 | Inspect EventBridge pipe criteria               |
| Action group invocations failing     | Lambda errors or permission issues   | Check CloudWatch logs for action group failures |

### Diagnostic Commands

```bash
# Lambda function logs
aws logs tail /aws/lambda/<intent-parser-fn> --follow
aws logs tail /aws/lambda/<image-analysis-fn> --follow
aws logs tail /aws/lambda/<data-enrichment-fn> --follow
aws logs tail /aws/lambda/<cultural-intelligence-fn> --follow

# DynamoDB inspection
aws dynamodb get-item --table-name <ProductsTable> --key '{"product_id":{"S":"<id>"}}'

# Bedrock Agent details
aws bedrock-agent get-agent --agent-id <BEDROCK_AGENT_ID>
aws bedrock-agent get-agent-alias --agent-id <AGENT_ID> --agent-alias-id <ALIAS_ID>

# Check action group configurations
aws bedrock-agent list-agent-action-groups --agent-id <BEDROCK_AGENT_ID> --agent-version DRAFT
```

---

## Roadmap

### Near-Term

- Structured prompt templates versioning
- Retry abstraction + DLQ compaction tooling
- Partial failure surfacing in status API

### Mid-Term

- Multi-platform trend sources (TikTok, Instagram)
- Content performance feedback loop
- Automated variant testing harness

### Long-Term

- **Multi-Agent Orchestration**: Custom-built agents with specialized training/fine-tuning for specific workflows
  - Vertical-specific agents (e-commerce, SaaS, retail, etc.)
  - Task-specialized agents (content creation, performance optimization, A/B testing)
  - Collaborative agent swarms for complex campaign strategies
- **Machine Learning Integration**: Accurate forecasting and predictive analytics
  - Campaign performance prediction models
  - Budget optimization and ROI forecasting
  - Audience behavior prediction
  - Trend detection and early adoption signals
- **Product Inventory Integration**: Agent access to real-time inventory data
  - Dynamic campaign adjustments based on stock levels
  - Automated product promotion prioritization
  - Inventory-aware content generation
  - Cross-sell and upsell recommendations
- Multi-tenant workspace segmentation
- Fine-tuned domain-specific generation models

---

## Contributing

### Workflow

1. Create feature branch: `git checkout -b feature/<name>`
2. Implement changes with tests
3. Run lint / formatting (add scripts if missing)
4. Validate Terraform plan in sandbox
5. Submit PR with concise description and impact notes

### Guidelines

- Prefer idempotent, stateless Lambda design
- Use environment variables over inline constants
- Keep prompts modular & parameterized
- Log structured JSON (avoid free-form strings)
- Document new Terraform modules with input/output blocks

---

## Support

| Channel                       | Purpose                 |
| ----------------------------- | ----------------------- |
| GitHub Issues                 | Bugs / feature requests |
| Slack (#ai-hackathon-support) | Internal coordination   |
| Email                         | Direct escalations      |

### Useful References

- [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Bedrock Agent Action Groups](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-create.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Amazon Bedrock Models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [EventBridge Pipes](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html)
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)

---

**Built with serverless + AI to accelerate marketing creativity.**

_Last Updated: October 20, 2025_
