# ===============================================
# Makefile for AWS AI Hackathon Project
# ===============================================

# Variables
PYTHON := python3
PIP := pip
REQUIREMENTS := requirements.txt
AWS := aws
AWS_REGION := eu-west-1
STACK_NAME := aws-ai-hackathon
S3_BUCKET := aws-ai-hackathon-$(shell date +%Y%m%d%H%M%S)
CFN_TEMPLATE := cloudformation_template.yaml
CODE_ZIP := lambda_code.zip
YOUTUBE_API_KEY ?= YOUR_YOUTUBE_API_KEY  # Set this via environment variable
BEDROCK_MODEL_ID ?= anthropic.claude-v2   # Set this via environment variable

.PHONY: all install run clean help build-lambda deploy-stack delete-stack test-local

# Default target
all: help

# Install dependencies from requirements.txt
install: $(REQUIREMENTS)
	@echo "--- Installing dependencies from $(REQUIREMENTS)..."
	$(PIP) install --upgrade -r $(REQUIREMENTS)
	@echo "--- Installation complete."

# Build Lambda deployment package
build-lambda:
	@echo "--- Building Lambda deployment package..."
	mkdir -p build
	# Install requirements to a local directory for packaging
	$(PIP) install -r $(REQUIREMENTS) --target ./build
	# Copy lambda files to build directory
	cp lambda_handler.py lambda_function.py campaign_generator.py campaign_function.py ./build/
	# Create zip file
	cd build && zip -r ../$(CODE_ZIP) .
	rm -rf build
	@echo "--- Lambda package $(CODE_ZIP) created."

# Test the lambda handler locally
test-lambda-local:
	@echo "--- Testing lambda_handler.py locally..."
	export ENRICHED_TABLE_NAME="EnrichedDataTable"; \
	export YOUTUBE_API_KEY="your-api-key-here"; \
	$(PYTHON) -c "import json; import lambda_function; event = json.load(open('test-event.json')); print(lambda_function.lambda_function_handler(event, None))"
	
# Run tests with mocked responses (for CI/CD)
test-lambda-mock:
	@echo "--- Running tests with mocked services..."
	# Mock environment variables and AWS services
	export MOCK_DYNAMODB=true; \
	export MOCK_YOUTUBE_API=true; \
	$(PYTHON) -c "import unittest; unittest.main(module='tests.test_lambda_handler', argv=['first-arg'])"

# Create S3 bucket for deployment
create-bucket:
	@echo "--- Creating S3 bucket for deployment..."
	$(AWS) s3 mb s3://$(S3_BUCKET) --region $(AWS_REGION)
	@echo "--- S3 bucket created: $(S3_BUCKET)"

# Deploy CloudFormation stack
deploy-stack: build-lambda create-bucket
	@echo "--- Uploading Lambda code to S3..."
	$(AWS) s3 cp $(CODE_ZIP) s3://$(S3_BUCKET)/$(CODE_ZIP)
	
	@echo "--- Deploying CloudFormation stack..."
	$(AWS) cloudformation deploy \
		--template-file $(CFN_TEMPLATE) \
		--stack-name $(STACK_NAME) \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			YouTubeApiKey=$(YOUTUBE_API_KEY) \
			BedrockModelId=$(BEDROCK_MODEL_ID)
	
	@echo "--- Updating Lambda functions with code..."
	# Get function names from CloudFormation outputs
	ENRICHMENT_LAMBDA=$$($(AWS) cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='EnrichmentLambdaARN'].OutputValue" --output text) && \
	CAMPAIGN_LAMBDA=$$($(AWS) cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='CampaignGeneratorLambdaARN'].OutputValue" --output text) && \
	$(AWS) lambda update-function-code --function-name $${ENRICHMENT_LAMBDA} --s3-bucket $(S3_BUCKET) --s3-key $(CODE_ZIP) && \
	$(AWS) lambda update-function-code --function-name $${CAMPAIGN_LAMBDA} --s3-bucket $(S3_BUCKET) --s3-key $(CODE_ZIP)
	
	@echo "--- Deployment complete."

# Delete CloudFormation stack
delete-stack:
	@echo "--- Deleting CloudFormation stack..."
	$(AWS) cloudformation delete-stack --stack-name $(STACK_NAME)
	@echo "--- Waiting for stack deletion to complete..."
	$(AWS) cloudformation wait stack-delete-complete --stack-name $(STACK_NAME)
	@echo "--- Stack deleted."

# Run test locally
test-local:
	@echo "--- Running local tests..."
	$(PYTHON) -c "import lambda_handler; print('Lambda handler loaded successfully')"
	$(PYTHON) -c "import campaign_generator; print('Campaign generator loaded successfully')"
	@echo "--- Tests complete."

# Run local script (YouTube API test)
run:
	@echo "--- Running the YouTube API test script..."
	$(PYTHON) fetch_trending_videos.py
	@echo "--- Script execution complete."

# Clean up temporary files
clean:
	@echo "--- Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f $(CODE_ZIP)
	@echo "--- Clean up complete."

# Display help message
help:
	@echo "==============================================="
	@echo "  AWS AI Hackathon Makefile"
	@echo "==============================================="
	@echo "  Commands:"
	@echo "  make install       - Installs/updates Python dependencies"
	@echo "  make build-lambda  - Builds Lambda deployment package"
	@echo "  make deploy-stack  - Deploys CloudFormation stack"
	@echo "  make delete-stack  - Deletes CloudFormation stack"
	@echo "  make test-local    - Tests Lambda code locally"
	@echo "  make run           - Runs YouTube API test script"
	@echo "  make clean         - Removes temporary files"
	@echo "  make help          - Displays this help message"
	@echo ""
	@echo "  Environment variables:"
	@echo "  YOUTUBE_API_KEY    - YouTube Data API v3 key"
	@echo "  BEDROCK_MODEL_ID   - Amazon Bedrock model ID"
	@echo "==============================================="

# This rule creates the requirements.txt file with the selected packages.
$(REQUIREMENTS):
	@echo "--- Generating $(REQUIREMENTS)..."
	@echo "google-api-python-client" > $(REQUIREMENTS)
	@echo "google-auth-oauthlib" >> $(REQUIREMENTS)
	@echo "google-auth-httplib2" >> $(REQUIREMENTS)
	@echo "dotenv" >> $(REQUIREMENTS)
	@echo "isodate" >> $(REQUIREMENTS)
	@echo "boto3" >> $(REQUIREMENTS)
	@echo "--- $(REQUIREMENTS) created."
