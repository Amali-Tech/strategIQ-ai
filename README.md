# AWS AI Hackathon - YouTube Enriched Marketing Campaign Generator

This project demonstrates an AI-driven marketing campaign generation system using AWS serverless services, YouTube Data API, and Amazon Bedrock.

## Architecture

This solution implements a two-phase architecture:

### Phase 1: Upload and Initial Analysis

- Web Application uploads images and product metadata to S3
- S3 triggers a Lambda function for initial analysis
- Lambda uses Rekognition to analyze images and stores results in DynamoDB Table 1
- Each image gets a unique base64 hash for later lookup

### Phase 2: Enrichment and Campaign Generation with EventBridge Pipe

- DynamoDB Table 1 stream feeds into an EventBridge Pipe
- The Pipe filters records with completed analysis
- **Enrichment Lambda** fetches related videos from YouTube Data API v3
- Enriched data is stored in DynamoDB Table 2
- EventBridge Pipe passes the enriched event to a target Lambda
- Target Lambda uses Amazon Bedrock to generate marketing campaigns
- Generated campaigns are stored back in DynamoDB Table 2

## Key Components

### EventBridge Pipe

The EventBridge Pipe connects DynamoDB streams to the enrichment Lambda and then to the target Lambda, creating a seamless data processing pipeline.

### Enrichment Lambda

The enrichment Lambda function (`lambda_handler.py`) is a crucial part of the process:

- Receives records from DynamoDB Table 1 via EventBridge Pipe
- Extracts product data and image analysis results
- Builds optimized search queries for YouTube
- Uses YouTube Data API v3 to find related videos
- Stores enriched data in DynamoDB Table 2
- Passes enriched events to the next stage

### Campaign Generator Lambda

The campaign generator Lambda (`campaign_generator.py`):

- Receives enriched events from the EventBridge Pipe
- Fetches full records from DynamoDB Table 2
- Builds detailed prompts including product info, image analysis, and YouTube trends
- Uses Amazon Bedrock to generate marketing campaign ideas
- Stores generated campaigns back in DynamoDB Table 2

## Deployment

### Prerequisites

- AWS account with appropriate permissions
- YouTube Data API v3 key
- Access to Amazon Bedrock service

### Setup

1. Clone this repository
2. Set up your YouTube API key as an environment variable:
   ```
   export YOUTUBE_API_KEY=your_api_key_here
   ```
3. Deploy the solution:
   ```
   make deploy-stack
   ```

### Cleanup

To remove all deployed resources:

```
make delete-stack
```

## Testing

1. Upload an image with metadata to the S3 bucket
2. Check DynamoDB Table 1 for initial analysis
3. Check DynamoDB Table 2 for enriched data and generated campaigns

## Local Development

You can test components locally:

```
make test-local
make run
```

## File Structure

- `lambda_handler.py`: YouTube enrichment Lambda function
- `campaign_generator.py`: Bedrock campaign generation Lambda function
- `cloudformation_template.yaml`: AWS CloudFormation template
- `fetch_trending_videos.py`: Utility for testing YouTube API locally
- `Makefile`: Build and deployment commands

## License

This project is licensed under the MIT License - see the LICENSE file for details.
