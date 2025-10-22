# StrategIQ Technical Architecture

## Overview

StrategIQ is a fully serverless, AI-driven marketing campaign generation platform built on AWS. The system transforms product images and campaign requirements into comprehensive, culturally-aware marketing strategies using Amazon Bedrock Agents with specialized action groups.

---

## Architecture Diagram

![StrategIQ Architecture](architecture-diagrams/images/hackathon-solution-architecture.jpg)

---

## System Workflow

### 1. Campaign Initiation & Secure Asset Upload

When you click **"Generate Campaign"**, the system doesn't ask for AWS credentials or force you to configure complex S3 buckets. Instead, it generates a **presigned URL** through API Gateway and a dedicated Lambda function.

**Why Presigned URLs?**

- **Security**: Temporary, time-limited access to upload directly to S3
- **Simplicity**: No AWS credential configuration needed on the client side
- **Performance**: Direct upload to S3 without proxy through backend servers
- **Cost Efficiency**: Reduces Lambda execution time and API Gateway payload limits

The presigned URL function generates a unique, secure upload link that's valid for a limited time (typically 15-60 minutes), allowing your client application to upload product images directly to the S3 bucket.

**Flow:**

```
User → API Gateway → Presigned URL Lambda → Returns Signed URL
User → Uploads Image Directly → S3 Bucket
```

---

### 2. Intent Parsing & Agent Invocation

Once the image is uploaded to S3, the object key (S3 path) along with your product information (name, description, category, target markets, campaign objectives) is sent to the **Intent Parser Lambda**.

This is the orchestration brain of the system. The Intent Parser:

1. **Receives the payload** containing:

   - S3 object key (location of uploaded image)
   - Product metadata (name, description, category)
   - Target markets (geographical regions)
   - Campaign objectives (awareness, engagement, conversion, etc.)

2. **Builds a context-rich prompt** for the Amazon Bedrock Agent:

   - Structures the product information
   - Formats the campaign requirements
   - Includes the S3 image location
   - Adds campaign objectives and target audience details

3. **Invokes the Bedrock Agent** with this comprehensive prompt

The Intent Parser acts as the **bridge** between your application and the intelligent AI agent, ensuring all necessary context is properly formatted and passed along.

**Flow:**

```
S3 Upload Complete → Intent Parser Lambda → Constructs Prompt → Invokes Bedrock Agent
```

---

### 3. Intelligent Action Group: Image Analysis

![Image Analysis Action Group](architecture-diagrams/images/hackathon-solution-architecture.jpg)

The Bedrock Agent, now equipped with your campaign requirements, **autonomously decides** it needs more visual insights about the product. This isn't hardcoded logic—the agent intelligently determines it should analyze the image to gain deeper context.

The agent makes a **tool call** to the **Image Analysis Action Group**:

**Image Analysis Handler Process:**

1. **Receives the request** from the Bedrock Agent containing:

   - Product information (name, description, category)
   - S3 bucket and object key

2. **Invokes Amazon Rekognition** (AWS's computer vision AI model):

   - Detects objects and labels in the image
   - Identifies product attributes (colors, shapes, materials)
   - Extracts any visible text (OCR)
   - Analyzes image composition and quality

3. **Returns enriched data** back to the agent:
   - Detected labels with confidence scores
   - Visual attributes
   - Product categorization insights
   - Marketing-relevant image characteristics

This gives the agent **visual intelligence**—it now understands not just what you told it about the product, but what it can "see" in the image.

**Flow:**

```
Bedrock Agent → Tool Call → Image Analysis Lambda → Amazon Rekognition API
                            ↓
                    Analyzes Image
                            ↓
                Returns: Labels, Attributes, Visual Insights
                            ↓
                    Bedrock Agent (enriched with visual context)
```

---

### 4. Data Enrichment: Market Intelligence

![Data Enrichment Action Group](architecture-diagrams/images/hackathon-solution-architecture.jpg)

Now armed with both your input and visual insights, the agent builds a **search query** to pull real-time market data. Again, this is an autonomous decision—the agent determines it needs current market trends to create a relevant, timely campaign.

The agent makes another **tool call** to the **Data Enrichment Action Group**:

**Data Enrichment Handler Process:**

1. **Constructs intelligent search queries** using:

   - Product name and category
   - Detected visual attributes
   - Target market information
   - Campaign objectives

2. **Queries the YouTube Data API v3** to fetch:

   - Trending videos related to the product category
   - Engagement metrics (views, likes, comments)
   - Popular content formats in your target market
   - Influencer and channel insights
   - Audience sentiment and preferences

3. **Analyzes and structures the data**:

   - Identifies trending content types
   - Calculates engagement scores
   - Extracts successful messaging patterns
   - Identifies optimal posting times and platforms

4. **Returns enriched market intelligence** to the agent:
   - Trending topics and hashtags
   - Successful campaign formats
   - Audience engagement patterns
   - Content recommendations

The agent now has **real-time market context**—it knows what's trending, what content performs well, and how audiences are engaging with similar products.

**Flow:**

```
Bedrock Agent → Builds Search Query → Tool Call → Data Enrichment Lambda
                                                        ↓
                                                YouTube Data API v3
                                                        ↓
                                        Fetch: Trends, Engagement, Content
                                                        ↓
                                        Returns: Market Intelligence
                                                        ↓
                                        Bedrock Agent (enriched with market data)
```

---

### 5. Cultural Intelligence: Market-Specific Adaptation

![Cultural Intelligence Action Group](architecture-diagrams/images/hackathon-solution-architecture.jpg)

The agent recognizes it needs to ensure the campaign fits within the **cultural and market context** of your target regions. This is critical—what works in North America might not resonate in Asia or Europe.

The agent makes a **tool call** to the **Cultural Intelligence Action Group**:

**Cultural Intelligence Handler Process:**

1. **Receives target market information** from the agent:

   - Target geographical regions
   - Product category
   - Campaign type (social media, email, etc.)

2. **Accesses the Knowledge Base**:

   - Structured cultural data stored in S3
   - Market-specific preferences and taboos
   - Color psychology by region
   - Cultural dimensions and communication styles
   - Regional holidays and events
   - Social media platform preferences by market

3. **Performs AI-powered cultural analysis** using Amazon Bedrock:

   - Analyzes cultural context for each target market
   - Generates communication guidelines
   - Identifies cultural sensitivities
   - Recommends market-specific adaptations

4. **Returns cultural insights** to the agent:
   - Market-specific messaging guidelines
   - Cultural do's and don'ts
   - Localization recommendations
   - Platform preferences by region
   - Timing recommendations based on local events

The agent now has **cultural intelligence**—it understands how to adapt the campaign to resonate with different cultural contexts, avoiding missteps and maximizing relevance.

**Flow:**

```
Bedrock Agent → Tool Call → Cultural Intelligence Lambda
                                    ↓
                    Accesses Knowledge Base (S3)
                                    ↓
                            Amazon Bedrock (Claude/Nova)
                                    ↓
                    Analyzes: Cultural Context, Market Preferences
                                    ↓
                    Returns: Cultural Insights, Guidelines
                                    ↓
                    Bedrock Agent (culturally aware)
```

---

### 6. Campaign Generation & Synthesis

The Bedrock Agent now has a **comprehensive understanding**:

- ✅ Your product details and campaign objectives (from your input)
- ✅ Visual attributes and insights (from Image Analysis)
- ✅ Real-time market trends and engagement data (from Data Enrichment)
- ✅ Cultural context and adaptation guidelines (from Cultural Intelligence)

The agent **autonomously synthesizes** all this information to generate a complete marketing campaign that includes:

**Campaign Deliverables:**

1. **Product Positioning**

   - Description optimized for each target market
   - Key selling points
   - Brand messaging

2. **Content Ideas** (2-5 platform-specific recommendations)

   - Platform (Instagram, TikTok, YouTube, LinkedIn, Twitter, Facebook)
   - Content topic and format
   - Engagement score prediction
   - Ready-to-use captions
   - Optimized hashtags

3. **Multi-Week Campaign Strategies**

   - Campaign name and duration
   - Posting frequency recommendations
   - Platform-specific adaptations
   - Week-by-week content calendar
   - Platform selection rationale

4. **Generated Assets**

   - Image generation prompts (for creating visual content)
   - Video scripts (short-form and long-form)
   - Email templates
   - Blog post outlines

5. **Market Intelligence**
   - Related YouTube videos (trending content for reference)
   - Platform recommendations with rationale
   - Cultural considerations by market
   - Audience preferences and trending content types

**The agent ensures:**

- JSON schema compliance (all required fields present)
- Cultural appropriateness for each target market
- Data-driven recommendations based on real engagement metrics
- Actionable, ready-to-implement campaign strategies

---

### 7. Optional: Competitive Intelligence (Premium Tier)

![Sentiment Analysis Action Group](architecture-diagrams/images/hackathon-solution-architecture.jpg)

Depending on your **pricing tier**, the system can perform competitor analysis. If you're on a premium plan and provide competitor URLs or product names:

**Sentiment Analysis Handler Process:**

1. **Searches for competitor content**:

   - YouTube videos about competitor products
   - Social media mentions
   - Customer reviews and feedback

2. **Analyzes sentiment** using AWS Comprehend:

   - Positive/negative/neutral sentiment breakdown
   - Confidence scores
   - Common themes and topics
   - Customer pain points and praise

3. **Generates competitive insights** using Bedrock:

   - How your product/campaign compares to competitors
   - Competitive advantages to highlight
   - Market gaps and opportunities
   - Actionable recommendations to differentiate

4. **Returns competitive analysis**:
   - Sentiment summary
   - Competitive positioning recommendations
   - Strategic action items

This gives you a **competitive edge**—understanding not just how to market your product, but how to position it against competitors in the market.

**Flow:**

```
Premium User → Provides Competitor URLs → Intent Parser
                                              ↓
                                    Sentiment Analysis Lambda
                                              ↓
                            YouTube API + AWS Comprehend
                                              ↓
                                    Amazon Bedrock (Analysis)
                                              ↓
                        Returns: Competitive Intelligence & Action Items
```

---

### 8. Campaign Delivery & Storage

Once the agent completes the synthesis:

1. **Campaign artifacts are stored** in DynamoDB:

   - Complete campaign JSON
   - Metadata (product_id, user_id, timestamps)
   - Processing status and correlation IDs

2. **Generated assets are stored** in S3:

   - Any generated images (if applicable)
   - Campaign documents
   - Asset references

3. **API returns the complete campaign** to your application:
   - Status: "completed"
   - Full campaign strategy
   - All generated content and recommendations
   - Ready for immediate implementation

---

## Key Architectural Principles

### 1. **Serverless Architecture**

- **No server management**: All compute runs on AWS Lambda
- **Auto-scaling**: Handles 1 request or 1,000,000 requests seamlessly
- **Pay-per-use**: Only pay for actual execution time
- **High availability**: AWS manages infrastructure reliability

### 2. **Event-Driven Design**

- **S3 Events**: Trigger processing on upload
- **DynamoDB Streams**: Enable real-time data flow (if configured)
- **EventBridge**: Orchestrates complex workflows
- **Asynchronous processing**: Non-blocking, responsive system

### 3. **AI-Driven Intelligence**

- **Amazon Bedrock Agents**: Autonomous decision-making
- **Action Groups**: Modular, specialized AI tools
- **Multi-modal AI**: Text (Claude/Nova) + Vision (Rekognition)
- **Knowledge-augmented generation**: Grounded in real data

### 4. **Security & Compliance**

- **Presigned URLs**: Temporary, scoped access
- **IAM roles**: Least-privilege access control
- **Encryption at rest**: S3 and DynamoDB encrypted
- **TLS in transit**: All API calls secured
- **No credential exposure**: Client never needs AWS keys

### 5. **Resilience & Graceful Degradation**

- **Single-call policy**: Each action group invoked once (no retry storms)
- **Partial data handling**: Agent generates campaigns even if some data is unavailable
- **Fallback strategies**: Uses foundational model knowledge when external APIs fail
- **Guaranteed output**: Always returns valid campaign JSON

---

## Technology Stack

| Component            | Technology                   | Purpose                                             |
| -------------------- | ---------------------------- | --------------------------------------------------- |
| **Orchestration**    | Amazon Bedrock Agent         | Intelligent campaign generation & tool coordination |
| **Vision AI**        | Amazon Rekognition           | Image analysis & label detection                    |
| **Language AI**      | Amazon Bedrock (Nova/Claude) | Campaign synthesis & cultural analysis              |
| **Sentiment AI**     | AWS Comprehend               | Competitor sentiment analysis                       |
| **Market Data**      | YouTube Data API v3          | Real-time trend intelligence                        |
| **Compute**          | AWS Lambda (Python 3.11)     | Serverless function execution                       |
| **Storage**          | Amazon S3                    | Image & asset storage                               |
| **Database**         | Amazon DynamoDB              | Campaign & metadata storage                         |
| **API Layer**        | Amazon API Gateway           | REST endpoints & presigned URL generation           |
| **Event Processing** | EventBridge                  | Event-driven workflow orchestration                 |
| **Monitoring**       | CloudWatch                   | Logs, metrics, and observability                    |
| **Infrastructure**   | Terraform                    | Infrastructure as Code                              |

---

## Data Flow Summary

```
User Input
    ↓
[1] Generate Presigned URL → Upload to S3
    ↓
[2] Intent Parser Lambda → Build Context
    ↓
[3] Bedrock Agent Invocation
    ↓
[4] Tool Call: Image Analysis → Rekognition → Visual Insights
    ↓
[5] Tool Call: Data Enrichment → YouTube API → Market Trends
    ↓
[6] Tool Call: Cultural Intelligence → Knowledge Base → Cultural Context
    ↓
[7] Agent Synthesis → Complete Campaign Generation
    ↓
[8] (Optional) Sentiment Analysis → Competitor Intelligence
    ↓
[9] Store in DynamoDB + S3
    ↓
[10] Return Campaign to User
```

---

## Performance Characteristics

| Operation                  | Typical Latency | Notes                               |
| -------------------------- | --------------- | ----------------------------------- |
| Presigned URL Generation   | < 500ms         | Lightweight Lambda function         |
| Image Upload to S3         | Variable        | Depends on image size and network   |
| Image Analysis             | 5-15s           | Rekognition processing time         |
| Data Enrichment            | 2-5s            | YouTube API query latency           |
| Cultural Intelligence      | 3-8s            | Knowledge base access + AI analysis |
| Campaign Synthesis         | 10-30s          | Bedrock model generation time       |
| End-to-End (no competitor) | 20-60s          | Full campaign generation            |
| With Competitor Analysis   | +5-15s          | Additional sentiment processing     |

---

## Scalability & Reliability

### Horizontal Scalability

- **Lambda concurrency**: Auto-scales to handle concurrent requests
- **S3**: Unlimited storage capacity
- **DynamoDB**: Auto-scaling read/write capacity
- **API Gateway**: Handles millions of requests per second

### Fault Tolerance

- **Retry logic**: Built into AWS SDK calls
- **Error handling**: Graceful degradation at each layer
- **CloudWatch monitoring**: Real-time error tracking
- **Correlation IDs**: End-to-end request tracing

### Cost Optimization

- **Pay-per-execution**: No idle server costs
- **Intelligent batching**: Efficient API usage
- **Caching strategies**: Reduce redundant API calls
- **Right-sized Lambdas**: Optimized memory allocation

---

## Security Architecture

### Authentication & Authorization

- **API Keys**: Basic authentication for REST endpoints
- **IAM Roles**: Service-to-service authentication
- **Presigned URLs**: Time-limited, scoped S3 access
- **No credential exposure**: Client-side security

### Data Protection

- **Encryption at Rest**: S3 SSE, DynamoDB encryption
- **Encryption in Transit**: TLS 1.2+ for all API calls
- **Secrets Management**: AWS Secrets Manager for API keys
- **Access Logging**: CloudTrail for audit trails

### Network Security

- **VPC Integration**: Lambda functions can run in VPC
- **Security Groups**: Network-level access control
- **WAF Ready**: Can add AWS WAF for API Gateway
- **DDoS Protection**: AWS Shield standard included

---

## Extensibility & Future Enhancements

The architecture is designed for growth:

### Planned Integrations

- **Multi-Agent Orchestration**: Specialized agents for specific verticals
- **Machine Learning**: Predictive analytics for campaign performance
- **Inventory Integration**: Real-time product availability awareness
- **Multi-Platform Trends**: TikTok, Instagram, Twitter APIs
- **Performance Feedback**: Closed-loop campaign optimization

### Easy Extension Points

- **New Action Groups**: Add specialized tools to the agent
- **Additional AI Models**: Integrate new Bedrock models
- **Custom Knowledge Bases**: Upload domain-specific data
- **Regional Expansion**: Add new market cultural data
- **Platform Integrations**: Connect to social media publishing APIs

---

**Built with ☁️ serverless architecture and 🤖 AI intelligence to revolutionize marketing campaign creation.**

_Architecture Document Version 1.0 | October 2025_
