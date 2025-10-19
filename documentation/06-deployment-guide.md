# Deployment Guide

## Overview

This guide covers deploying the Degenerals Marketing Intelligence Platform using Terraform and AWS services.

## Prerequisites

### Required Tools

1. **Terraform** (>= 1.0)

```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version
```

2. **AWS CLI** (>= 2.0)

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

3. **Python** (>= 3.9)

```bash
python3 --version
pip3 --version
```

### AWS Account Setup

1. **Create AWS Account**: If you don't have one
2. **Configure AWS CLI**:

```bash
aws configure --profile sandbox-034
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: eu-west-1
# - Default output format: json
```

3. **Verify Access**:

```bash
aws sts get-caller-identity --profile sandbox-034
```

### Required AWS Permissions

Your IAM user/role needs:

- Lambda: Full access
- API Gateway: Full access
- DynamoDB: Full access
- S3: Full access
- SQS: Full access
- Bedrock: Model invocation
- Rekognition: Full access
- IAM: Role creation and policy management
- CloudWatch: Logs and metrics

## Project Structure

```
degenerals-com/
├── degenerals-infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       ├── modules/
│       │   ├── api-gateway/
│       │   ├── dynamodb/
│       │   ├── lambda/
│       │   ├── s3/
│       │   └── sqs/
│       └── lambda-handlers/
│           ├── intent_parser/
│           ├── image-analysis/
│           ├── data-enrichment/
│           ├── cultural-intelligence/
│           ├── generate-images/
│           └── image-generation-status/
└── documentations/
```

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/degenerals-com.git
cd degenerals-com/degenerals-infra/terraform
```

### 2. Configure Variables

Edit `terraform.tfvars`:

```hcl
# AWS Configuration
aws_region  = "eu-west-1"
aws_profile = "sandbox-034"

# Project Configuration
project_name = "degenerals-mi"
environment  = "dev"
project_root = "/home/solomon/labs/degenerals-com/degenerals-infra"

# API Keys
youtube_api_key = "YOUR_YOUTUBE_API_KEY"  # Get from Google Cloud Console

# DynamoDB Table Names
products_table_name         = "products"
generated_images_table_name = "generated_images"

# SQS Queue Name
image_generation_queue_name = "image-generation-queue"

# Lambda Function Names
lambda_image_analysis_function_name       = "image-analysis-lambda"
lambda_data_enrichment_function_name      = "data-enrichment-lambda"
lambda_cultural_intelligence_function_name = "cultural-intelligence-lambda"
lambda_intent_parser_function_name        = "intent-parser-lambda"
```

### 3. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict API key to YouTube Data API v3
6. Copy the API key to `terraform.tfvars`

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd degenerals-infra/terraform
terraform init
```

**Expected Output**:

```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 2: Plan Deployment

```bash
terraform plan
```

Review the planned changes. You should see resources for:

- 6 Lambda functions
- 2 DynamoDB tables
- 2 S3 buckets
- 1 SQS queue
- 1 API Gateway
- Multiple IAM roles and policies

### Step 3: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

**Deployment Time**: ~5-10 minutes

**Expected Output**:

```
Apply complete! Resources: 45 added, 0 changed, 0 destroyed.

Outputs:
api_gateway_url = "https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev"
dynamodb_tables = {
  "generated_images" = "arn:aws:dynamodb:..."
  "products" = "arn:aws:dynamodb:..."
}
...
```

### Step 4: Verify Deployment

```bash
# Test API Gateway
curl https://YOUR_API_GATEWAY_URL/dev/api/campaign/tier-1

# List Lambda functions
aws lambda list-functions --profile sandbox-034 --region eu-west-1

# Check DynamoDB tables
aws dynamodb list-tables --profile sandbox-034 --region eu-west-1

# Check S3 buckets
aws s3 ls --profile sandbox-034 --region eu-west-1
```

## Post-Deployment Configuration

### 1. Enable Bedrock Model Access

1. Go to AWS Bedrock Console
2. Navigate to Model access
3. Request access to:
   - Amazon Nova Pro
   - Amazon Nova Canvas
4. Wait for approval (~5 minutes)

### 2. Configure S3 Bucket Policies

#### Make Generated Assets Public

```bash
aws s3api put-bucket-policy \
  --bucket degenerals-mi-dev-generated-assets \
  --policy file://bucket-policy.json \
  --profile sandbox-034 \
  --region eu-west-1
```

`bucket-policy.json`:

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

### 3. Create API Gateway → SQS IAM Role

```bash
# Create role
aws iam create-role \
  --role-name apigateway-sqs-invoke-role \
  --assume-role-policy-document file://trust-policy.json \
  --profile sandbox-034

# Attach policy
aws iam attach-role-policy \
  --role-name apigateway-sqs-invoke-role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/apigateway-sqs-invoke-role \
  --profile sandbox-034
```

`trust-policy.json`:

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

### 4. Update SQS Queue Policy

```bash
aws sqs set-queue-attributes \
  --queue-url https://sqs.eu-west-1.amazonaws.com/YOUR_ACCOUNT_ID/degenerals-mi-dev-image-generation-queue \
  --attributes file://queue-policy.json \
  --profile sandbox-034 \
  --region eu-west-1
```

`queue-policy.json`:

```json
{
  "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"__owner_statement\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::YOUR_ACCOUNT_ID:root\"},\"Action\":\"SQS:*\",\"Resource\":\"arn:aws:sqs:eu-west-1:YOUR_ACCOUNT_ID:degenerals-mi-dev-image-generation-queue\"},{\"Sid\":\"AllowAPIGatewayToSend\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::YOUR_ACCOUNT_ID:role/apigateway-sqs-invoke-role\"},\"Action\":\"sqs:SendMessage\",\"Resource\":\"arn:aws:sqs:eu-west-1:YOUR_ACCOUNT_ID:degenerals-mi-dev-image-generation-queue\"}]}"
}
```

### 5. Update Lambda Environment Variables

```bash
# Update generate-images Lambda
aws lambda update-function-configuration \
  --function-name degenerals-mi-dev-generate-images \
  --environment Variables={S3_BUCKET_NAME=degenerals-mi-dev-generated-assets,DYNAMODB_TABLE_NAME=generated_images} \
  --profile sandbox-034 \
  --region eu-west-1

# Update image-generation-status Lambda
aws lambda update-function-configuration \
  --function-name degenerals-mi-dev-image-generation-status \
  --environment Variables={DYNAMODB_TABLE_NAME=generated_images} \
  --profile sandbox-034 \
  --region eu-west-1
```

## Testing Deployment

### 1. Test Campaign Generation

```bash
curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/campaign/tier-1 \
  -H "Content-Type: application/json" \
  -d '{
    "product_info": {
      "name": "Test Product",
      "description": "Test description for deployment verification",
      "category": "electronics"
    },
    "s3_info": {
      "bucket": "degenerals-mi-dev-images",
      "key": "test/sample.jpg"
    },
    "target_markets": {
      "markets": ["North America"]
    },
    "campaign_objectives": {
      "target_audience": "General consumers",
      "campaign_duration": "30 days",
      "primary_goal": "Increase awareness"
    }
  }'
```

### 2. Test Image Generation

```bash
# Submit request
curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "style": "natural",
    "aspect_ratio": "16:9",
    "request_id": "test-123"
  }'

# Check status
curl https://YOUR_API_GATEWAY_URL/dev/api/assets/test-123
```

### 3. Test Upload Flow

```bash
# Get presigned URL
RESPONSE=$(curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/upload/presigned-url \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "test.jpg",
    "file_type": "image/jpeg"
  }')

echo $RESPONSE | jq .

# Upload file (use the URL from response)
curl -X PUT "PRESIGNED_URL_HERE" \
  -H "Content-Type: image/jpeg" \
  --data-binary @test.jpg

# Check status
curl https://YOUR_API_GATEWAY_URL/dev/api/upload/status/UPLOAD_ID_HERE
```

## Environment-Specific Deployments

### Development Environment

```hcl
# terraform.tfvars
environment = "dev"
```

```bash
terraform workspace new dev
terraform workspace select dev
terraform apply
```

### Staging Environment

```hcl
# terraform-staging.tfvars
environment = "staging"
project_name = "degenerals-mi"
# ... other staging-specific configs
```

```bash
terraform workspace new staging
terraform workspace select staging
terraform apply -var-file="terraform-staging.tfvars"
```

### Production Environment

```hcl
# terraform-prod.tfvars
environment = "prod"
project_name = "degenerals-mi"
# ... other production-specific configs
```

```bash
terraform workspace new prod
terraform workspace select prod
terraform apply -var-file="terraform-prod.tfvars"
```

## Updating Deployments

### Update Lambda Function Code

```bash
# Navigate to Lambda handler directory
cd degenerals-infra/terraform/lambda-handlers/generate-images

# Make code changes
vim handler.py

# Re-deploy with Terraform
cd ../../
terraform apply -target=module.lambda.aws_lambda_function.generate_images
```

### Update Infrastructure

```bash
# Make Terraform changes
vim main.tf

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Rolling Updates

```bash
# Update only specific resources
terraform apply -target=module.api_gateway
terraform apply -target=module.lambda.aws_lambda_function.intent_parser
```

## Rollback Procedures

### Rollback to Previous State

```bash
# List state backups
ls -la terraform.tfstate.backup*

# Restore previous state
cp terraform.tfstate terraform.tfstate.current
cp terraform.tfstate.backup terraform.tfstate

# Apply previous state
terraform apply
```

### Rollback Lambda Function

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name degenerals-mi-dev-generate-images \
  --profile sandbox-034

# Update alias to previous version
aws lambda update-alias \
  --function-name degenerals-mi-dev-generate-images \
  --name live \
  --function-version 3 \
  --profile sandbox-034
```

## Monitoring Deployment

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/degenerals-mi-dev-generate-images \
  --follow \
  --profile sandbox-034 \
  --region eu-west-1
```

### CloudWatch Metrics

```bash
# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=degenerals-mi-dev-generate-images \
  --start-time 2025-10-19T00:00:00Z \
  --end-time 2025-10-19T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --profile sandbox-034 \
  --region eu-west-1
```

## Cost Optimization

### Monitor Costs

```bash
# Get cost and usage
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --profile sandbox-034
```

### Set Billing Alarms

````bash
# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name degenerals-billing-alarm \
  --alarm-description "Alert when monthly costs exceed $100" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThan// filepath: /home/solomon/labs/degenerals-com/documentations/06-deployment-guide.md
# Deployment Guide

## Overview

This guide covers deploying the Degenerals Marketing Intelligence Platform using Terraform and AWS services.

## Prerequisites

### Required Tools

1. **Terraform** (>= 1.0)
```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version
````

2. **AWS CLI** (>= 2.0)

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

3. **Python** (>= 3.9)

```bash
python3 --version
pip3 --version
```

### AWS Account Setup

1. **Create AWS Account**: If you don't have one
2. **Configure AWS CLI**:

```bash
aws configure --profile sandbox-034
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: eu-west-1
# - Default output format: json
```

3. **Verify Access**:

```bash
aws sts get-caller-identity --profile sandbox-034
```

### Required AWS Permissions

Your IAM user/role needs:

- Lambda: Full access
- API Gateway: Full access
- DynamoDB: Full access
- S3: Full access
- SQS: Full access
- Bedrock: Model invocation
- Rekognition: Full access
- IAM: Role creation and policy management
- CloudWatch: Logs and metrics

## Project Structure

```
degenerals-com/
├── degenerals-infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       ├── modules/
│       │   ├── api-gateway/
│       │   ├── dynamodb/
│       │   ├── lambda/
│       │   ├── s3/
│       │   └── sqs/
│       └── lambda-handlers/
│           ├── intent_parser/
│           ├── image-analysis/
│           ├── data-enrichment/
│           ├── cultural-intelligence/
│           ├── generate-images/
│           └── image-generation-status/
└── documentations/
```

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/degenerals-com.git
cd degenerals-com/degenerals-infra/terraform
```

### 2. Configure Variables

Edit `terraform.tfvars`:

```hcl
# AWS Configuration
aws_region  = "eu-west-1"
aws_profile = "sandbox-034"

# Project Configuration
project_name = "degenerals-mi"
environment  = "dev"
project_root = "/home/solomon/labs/degenerals-com/degenerals-infra"

# API Keys
youtube_api_key = "YOUR_YOUTUBE_API_KEY"  # Get from Google Cloud Console

# DynamoDB Table Names
products_table_name         = "products"
generated_images_table_name = "generated_images"

# SQS Queue Name
image_generation_queue_name = "image-generation-queue"

# Lambda Function Names
lambda_image_analysis_function_name       = "image-analysis-lambda"
lambda_data_enrichment_function_name      = "data-enrichment-lambda"
lambda_cultural_intelligence_function_name = "cultural-intelligence-lambda"
lambda_intent_parser_function_name        = "intent-parser-lambda"
```

### 3. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict API key to YouTube Data API v3
6. Copy the API key to `terraform.tfvars`

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd degenerals-infra/terraform
terraform init
```

**Expected Output**:

```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 2: Plan Deployment

```bash
terraform plan
```

Review the planned changes. You should see resources for:

- 6 Lambda functions
- 2 DynamoDB tables
- 2 S3 buckets
- 1 SQS queue
- 1 API Gateway
- Multiple IAM roles and policies

### Step 3: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

**Deployment Time**: ~5-10 minutes

**Expected Output**:

```
Apply complete! Resources: 45 added, 0 changed, 0 destroyed.

Outputs:
api_gateway_url = "https://u4xf9rvuwj.execute-api.eu-west-1.amazonaws.com/dev"
dynamodb_tables = {
  "generated_images" = "arn:aws:dynamodb:..."
  "products" = "arn:aws:dynamodb:..."
}
...
```

### Step 4: Verify Deployment

```bash
# Test API Gateway
curl https://YOUR_API_GATEWAY_URL/dev/api/campaign/tier-1

# List Lambda functions
aws lambda list-functions --profile sandbox-034 --region eu-west-1

# Check DynamoDB tables
aws dynamodb list-tables --profile sandbox-034 --region eu-west-1

# Check S3 buckets
aws s3 ls --profile sandbox-034 --region eu-west-1
```

## Post-Deployment Configuration

### 1. Enable Bedrock Model Access

1. Go to AWS Bedrock Console
2. Navigate to Model access
3. Request access to:
   - Amazon Nova Pro
   - Amazon Nova Canvas
4. Wait for approval (~5 minutes)

### 2. Configure S3 Bucket Policies

#### Make Generated Assets Public

```bash
aws s3api put-bucket-policy \
  --bucket degenerals-mi-dev-generated-assets \
  --policy file://bucket-policy.json \
  --profile sandbox-034 \
  --region eu-west-1
```

`bucket-policy.json`:

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

### 3. Create API Gateway → SQS IAM Role

```bash
# Create role
aws iam create-role \
  --role-name apigateway-sqs-invoke-role \
  --assume-role-policy-document file://trust-policy.json \
  --profile sandbox-034

# Attach policy
aws iam attach-role-policy \
  --role-name apigateway-sqs-invoke-role \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/apigateway-sqs-invoke-role \
  --profile sandbox-034
```

`trust-policy.json`:

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

### 4. Update SQS Queue Policy

```bash
aws sqs set-queue-attributes \
  --queue-url https://sqs.eu-west-1.amazonaws.com/YOUR_ACCOUNT_ID/degenerals-mi-dev-image-generation-queue \
  --attributes file://queue-policy.json \
  --profile sandbox-034 \
  --region eu-west-1
```

`queue-policy.json`:

```json
{
  "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"__owner_statement\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::YOUR_ACCOUNT_ID:root\"},\"Action\":\"SQS:*\",\"Resource\":\"arn:aws:sqs:eu-west-1:YOUR_ACCOUNT_ID:degenerals-mi-dev-image-generation-queue\"},{\"Sid\":\"AllowAPIGatewayToSend\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::YOUR_ACCOUNT_ID:role/apigateway-sqs-invoke-role\"},\"Action\":\"sqs:SendMessage\",\"Resource\":\"arn:aws:sqs:eu-west-1:YOUR_ACCOUNT_ID:degenerals-mi-dev-image-generation-queue\"}]}"
}
```

### 5. Update Lambda Environment Variables

```bash
# Update generate-images Lambda
aws lambda update-function-configuration \
  --function-name degenerals-mi-dev-generate-images \
  --environment Variables={S3_BUCKET_NAME=degenerals-mi-dev-generated-assets,DYNAMODB_TABLE_NAME=generated_images} \
  --profile sandbox-034 \
  --region eu-west-1

# Update image-generation-status Lambda
aws lambda update-function-configuration \
  --function-name degenerals-mi-dev-image-generation-status \
  --environment Variables={DYNAMODB_TABLE_NAME=generated_images} \
  --profile sandbox-034 \
  --region eu-west-1
```

## Testing Deployment

### 1. Test Campaign Generation

```bash
curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/campaign/tier-1 \
  -H "Content-Type: application/json" \
  -d '{
    "product_info": {
      "name": "Test Product",
      "description": "Test description for deployment verification",
      "category": "electronics"
    },
    "s3_info": {
      "bucket": "degenerals-mi-dev-images",
      "key": "test/sample.jpg"
    },
    "target_markets": {
      "markets": ["North America"]
    },
    "campaign_objectives": {
      "target_audience": "General consumers",
      "campaign_duration": "30 days",
      "primary_goal": "Increase awareness"
    }
  }'
```

### 2. Test Image Generation

```bash
# Submit request
curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "style": "natural",
    "aspect_ratio": "16:9",
    "request_id": "test-123"
  }'

# Check status
curl https://YOUR_API_GATEWAY_URL/dev/api/assets/test-123
```

### 3. Test Upload Flow

```bash
# Get presigned URL
RESPONSE=$(curl -X POST https://YOUR_API_GATEWAY_URL/dev/api/upload/presigned-url \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "test.jpg",
    "file_type": "image/jpeg"
  }')

echo $RESPONSE | jq .

# Upload file (use the URL from response)
curl -X PUT "PRESIGNED_URL_HERE" \
  -H "Content-Type: image/jpeg" \
  --data-binary @test.jpg

# Check status
curl https://YOUR_API_GATEWAY_URL/dev/api/upload/status/UPLOAD_ID_HERE
```

## Environment-Specific Deployments

### Development Environment

```hcl
# terraform.tfvars
environment = "dev"
```

```bash
terraform workspace new dev
terraform workspace select dev
terraform apply
```

### Staging Environment

```hcl
# terraform-staging.tfvars
environment = "staging"
project_name = "degenerals-mi"
# ... other staging-specific configs
```

```bash
terraform workspace new staging
terraform workspace select staging
terraform apply -var-file="terraform-staging.tfvars"
```

### Production Environment

```hcl
# terraform-prod.tfvars
environment = "prod"
project_name = "degenerals-mi"
# ... other production-specific configs
```

```bash
terraform workspace new prod
terraform workspace select prod
terraform apply -var-file="terraform-prod.tfvars"
```

## Updating Deployments

### Update Lambda Function Code

```bash
# Navigate to Lambda handler directory
cd degenerals-infra/terraform/lambda-handlers/generate-images

# Make code changes
vim handler.py

# Re-deploy with Terraform
cd ../../
terraform apply -target=module.lambda.aws_lambda_function.generate_images
```

### Update Infrastructure

```bash
# Make Terraform changes
vim main.tf

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Rolling Updates

```bash
# Update only specific resources
terraform apply -target=module.api_gateway
terraform apply -target=module.lambda.aws_lambda_function.intent_parser
```

## Rollback Procedures

### Rollback to Previous State

```bash
# List state backups
ls -la terraform.tfstate.backup*

# Restore previous state
cp terraform.tfstate terraform.tfstate.current
cp terraform.tfstate.backup terraform.tfstate

# Apply previous state
terraform apply
```

### Rollback Lambda Function

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name degenerals-mi-dev-generate-images \
  --profile sandbox-034

# Update alias to previous version
aws lambda update-alias \
  --function-name degenerals-mi-dev-generate-images \
  --name live \
  --function-version 3 \
  --profile sandbox-034
```

## Monitoring Deployment

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/degenerals-mi-dev-generate-images \
  --follow \
  --profile sandbox-034 \
  --region eu-west-1
```

### CloudWatch Metrics

```bash
# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=degenerals-mi-dev-generate-images \
  --start-time 2025-10-19T00:00:00Z \
  --end-time 2025-10-19T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --profile sandbox-034 \
  --region eu-west-1
```

## Cost Optimization

### Monitor Costs

```bash
# Get cost and usage
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --profile sandbox-034
```

### Set Billing Alarms

```bash
# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name degenerals-billing-alarm \
  --alarm-description "Alert when monthly costs exceed $100" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThan
```
