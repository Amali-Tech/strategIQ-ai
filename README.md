# Degenerals Marketing Intelligence Platform - Documentation

## Overview

This documentation covers the complete architecture and workflows of the Degenerals Marketing Intelligence Platform, an AI-powered system for generating viral marketing campaigns.

## Table of Contents

1. [Architecture Overview](./documentation/architecture-diagrams/images/01-architecture-overview.md)
2. [Campaign Generation Workflow](./documentation/architecture-diagrams/images/02-campaign-generation-workflow.md)
3. [Image Generation Workflow](./documentation/architecture-diagrams/images/03-image-generation-workflow.md)
4. [Data Flow and Integration](./documentation/architecture-diagrams/images/04-data-flow-integration.md)
5. [API Reference](./documentation/architecture-diagrams/images/05-api-reference.md)
6. [Deployment Guide](./documentation/architecture-diagrams/images/06-deployment-guide.md)
7. [Troubleshooting](./documentation/architecture-diagrams/images/07-troubleshooting.md)

## Quick Links

- **Infrastructure Code**: `/degenerals-infra/terraform/`
- **Lambda Functions**: `/degenerals-infra/terraform/lambda-handlers/`
- **API Gateway**: `/degenerals-infra/terraform/modules/api-gateway/`

## System Components

### Core Services

- **API Gateway**: HTTP API endpoint for client requests
- **Lambda Functions**: Serverless compute for processing
- **Bedrock**: AI/ML model inference (Nova Pro, Nova Canvas)
- **DynamoDB**: NoSQL database for metadata storage
- **S3**: Object storage for images and assets
- **SQS**: Message queue for async processing

### Key Workflows

1. Campaign generation with AI analysis
2. Asynchronous image generation
3. Multi-source data enrichment
4. Cultural intelligence integration
