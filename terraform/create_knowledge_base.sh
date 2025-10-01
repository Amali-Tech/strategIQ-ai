#!/bin/bash

# create_knowledge_base.sh - Helper script to create a Bedrock Knowledge Base

set -e

echo "🧠 Lokalize Knowledge Base Creator"
echo "================================="

# Ensure AWS profile is set
if [ -z "$AWS_PROFILE" ]; then
    echo "📋 Available AWS profiles:"
    aws configure list-profiles 2>/dev/null || echo "  (No profiles found)"
    read -p "Enter AWS profile name: " AWS_PROFILE
    export AWS_PROFILE
fi

if [ -z "$AWS_REGION" ]; then
    AWS_REGION=$(aws configure get region --profile $AWS_PROFILE 2>/dev/null || echo "us-west-2")
    export AWS_REGION
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)

echo "Using Profile: $AWS_PROFILE"
echo "Region: $AWS_REGION" 
echo "Account: $AWS_ACCOUNT_ID"
echo ""

# Check if Knowledge Bases exist
echo "🔍 Checking existing Knowledge Bases..."
EXISTING_KBS=$(aws bedrock-agent list-knowledge-bases --profile $AWS_PROFILE --region $AWS_REGION --query 'knowledgeBaseSummaries[?contains(name, `lokalize`) || contains(name, `cultural`)].{Name:name,Id:knowledgeBaseId}' --output table 2>/dev/null || echo "No existing knowledge bases found")

echo "$EXISTING_KBS"
echo ""

read -p "Do you want to create a new Knowledge Base? (y/n): " create_new

if [ "$create_new" != "y" ] && [ "$create_new" != "Y" ]; then
    echo "Please provide an existing Knowledge Base ID:"
    read -p "Knowledge Base ID: " KB_ID
    
    # Validate the KB ID
    if aws bedrock-agent get-knowledge-base --knowledge-base-id $KB_ID --profile $AWS_PROFILE --region $AWS_REGION >/dev/null 2>&1; then
        echo "✅ Knowledge Base $KB_ID is accessible"
        echo "export KNOWLEDGE_BASE_ID=$KB_ID" >> .env
        echo "💾 Added KNOWLEDGE_BASE_ID to .env file"
    else
        echo "❌ Cannot access Knowledge Base $KB_ID"
        exit 1
    fi
    exit 0
fi

# Create S3 bucket for documents
BUCKET_NAME="lokalize-cultural-docs-$AWS_ACCOUNT_ID"
echo "📦 Creating S3 bucket: $BUCKET_NAME"

if aws s3 ls "s3://$BUCKET_NAME" --profile $AWS_PROFILE >/dev/null 2>&1; then
    echo "✅ Bucket already exists"
else
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3 mb "s3://$BUCKET_NAME" --profile $AWS_PROFILE
    else
        aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION --profile $AWS_PROFILE
    fi
    echo "✅ Created S3 bucket: $BUCKET_NAME"
fi

# Create sample cultural documents
echo "📝 Creating sample cultural documents..."
mkdir -p sample-docs/regions
mkdir -p sample-docs/best-practices

cat > sample-docs/regions/general-cultural-guidelines.md << 'EOF'
# General Cultural Marketing Guidelines

## Universal Principles
- Respect local customs and traditions
- Avoid stereotypes and generalizations
- Consider religious and cultural sensitivities
- Adapt visual elements (colors, imagery) appropriately

## High-Context vs Low-Context Cultures
- High-context (Japan, Middle East): Implicit communication, relationship-focused
- Low-context (Germany, Nordics): Direct communication, fact-focused

## Religious Considerations
- Islamic markets: Halal requirements, Ramadan timing, modest imagery
- Christian markets: Easter/Christmas timing, family values
- Buddhist markets: Karma concepts, respectful imagery
- Secular markets: Focus on individual benefits

## Color Psychology by Culture
- Red: Good luck (China), Danger (West), Purity (India)
- White: Purity (West), Death/Mourning (East Asia)
- Green: Nature (West), Sacred (Islam), Fertility (many cultures)
- Blue: Trust (global), Masculinity (West), Immortality (Egypt)

## Common Cultural Mistakes to Avoid
- Using wrong hand gestures
- Inappropriate religious references
- Gender role assumptions
- Seasonal misalignment
- Currency/pricing mistakes
EOF

cat > sample-docs/best-practices/marketing-localization-checklist.md << 'EOF'
# Marketing Localization Checklist

## Content Review
- [ ] Language appropriate for target market
- [ ] Cultural references understood locally
- [ ] Religious sensitivities addressed
- [ ] Gender roles culturally appropriate
- [ ] Age demographics considered

## Visual Elements
- [ ] Colors culturally appropriate
- [ ] Images reflect local demographics
- [ ] Symbols/icons culturally relevant
- [ ] Text direction (LTR/RTL) correct

## Timing and Seasonality
- [ ] Launch timing considers local holidays
- [ ] Seasonal relevance checked
- [ ] Religious observances respected
- [ ] Local business cycles considered

## Legal and Regulatory
- [ ] Advertising standards compliance
- [ ] Data privacy laws (GDPR, etc.)
- [ ] Product claims legally valid
- [ ] Age restrictions appropriate

## Measurement and Testing
- [ ] Local market research conducted
- [ ] A/B testing with cultural variants
- [ ] Local focus groups consulted
- [ ] Performance metrics culturally relevant
EOF

# Upload sample documents
echo "📤 Uploading sample documents to S3..."
aws s3 cp sample-docs/ "s3://$BUCKET_NAME/cultural-guidelines/" --recursive --profile $AWS_PROFILE
echo "✅ Uploaded sample documents"

# Clean up local files
rm -rf sample-docs/

echo ""
echo "🏗️ Now create your Knowledge Base manually via AWS Console:"
echo ""
echo "1. Go to: https://$AWS_REGION.console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/knowledge-bases"
echo "2. Click 'Create knowledge base'"
echo "3. Name: 'lokalize-cultural-intelligence'"
echo "4. Data source: S3 bucket '$BUCKET_NAME'"
echo "5. Embedding model: amazon.titan-embed-text-v1"
echo "6. Vector store: Amazon OpenSearch Serverless"
echo ""
echo "After creation, add the Knowledge Base ID to your deployment:"
echo "export KNOWLEDGE_BASE_ID=YOUR_NEW_KB_ID"
echo ""
echo "📚 Sample documents are now in: s3://$BUCKET_NAME/cultural-guidelines/"