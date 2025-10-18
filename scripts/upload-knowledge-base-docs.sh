#!/bin/bash

# Script to upload knowledge base documents to S3
# This script syncs the local knowledge-bases directory with the S3 bucket

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KNOWLEDGE_BASES_DIR="$PROJECT_ROOT/knowledge-bases"

# AWS Profile and Region (can be overridden by environment variables)
AWS_PROFILE=${AWS_PROFILE:-"sandbox-034"}
AWS_REGION=${AWS_REGION:-"eu-west-1"}

# Project configuration
PROJECT_NAME="degenerals-mi"
ENVIRONMENT="dev"
BUCKET_NAME="${PROJECT_NAME}-${ENVIRONMENT}-knowledge-base-docs"

echo "🚀 Starting Knowledge Base Document Upload"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo "Bucket: $BUCKET_NAME"
echo "Source Directory: $KNOWLEDGE_BASES_DIR"
echo "AWS Profile: $AWS_PROFILE"
echo "AWS Region: $AWS_REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if knowledge bases directory exists
if [ ! -d "$KNOWLEDGE_BASES_DIR" ]; then
    echo "❌ Knowledge bases directory not found: $KNOWLEDGE_BASES_DIR"
    exit 1
fi

# Check if S3 bucket exists
echo "🔍 Checking if S3 bucket exists..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE" 2>/dev/null; then
    echo "✅ S3 bucket $BUCKET_NAME exists"
else
    echo "❌ S3 bucket $BUCKET_NAME does not exist or is not accessible"
    echo "Please run 'terraform apply' first to create the infrastructure"
    exit 1
fi

# Function to upload files with proper content type
upload_files() {
    local source_dir="$1"
    local s3_prefix="$2"
    local description="$3"
    
    echo "📁 Uploading $description..."
    
    # Find all files in the directory
    find "$source_dir" -type f | while read -r file; do
        # Get relative path from source directory
        relative_path=$(realpath --relative-to="$source_dir" "$file")
        s3_key="$s3_prefix/$relative_path"
        
        # Determine content type based on file extension
        case "${file##*.}" in
            "md"|"txt")
                content_type="text/plain"
                ;;
            "csv")
                content_type="text/csv"
                ;;
            "json")
                content_type="application/json"
                ;;
            *)
                content_type="text/plain"
                ;;
        esac
        
        echo "  📄 Uploading: $relative_path -> s3://$BUCKET_NAME/$s3_key"
        
        # Upload file to S3 with proper content type and metadata
        aws s3 cp "$file" "s3://$BUCKET_NAME/$s3_key" \
            --profile "$AWS_PROFILE" \
            --content-type "$content_type" \
            --metadata "source=knowledge-base,category=$s3_prefix,upload-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --quiet
    done
}

# Upload cross-cultural files
if [ -d "$KNOWLEDGE_BASES_DIR/cross-cultural" ]; then
    upload_files "$KNOWLEDGE_BASES_DIR/cross-cultural" "cross-cultural" "Cross-Cultural Adaptation Guidelines"
else
    echo "⚠️  Cross-cultural directory not found, skipping..."
fi

# Upload market-specific files
if [ -d "$KNOWLEDGE_BASES_DIR/markets" ]; then
    upload_files "$KNOWLEDGE_BASES_DIR/markets" "markets" "Market-Specific Intelligence"
else
    echo "⚠️  Markets directory not found, skipping..."
fi

echo ""
echo "📊 Upload Summary:"
echo "=================="

# Get object count and total size
total_objects=$(aws s3api list-objects-v2 --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE" --query 'KeyCount' --output text 2>/dev/null || echo "0")
total_size=$(aws s3api list-objects-v2 --bucket "$BUCKET_NAME" --profile "$AWS_PROFILE" --query 'sum(Contents[].Size)' --output text 2>/dev/null || echo "0")

# Convert bytes to human readable format
if [ "$total_size" != "0" ] && [ "$total_size" != "null" ]; then
    if [ "$total_size" -gt 1048576 ]; then
        size_display=$(echo "scale=2; $total_size / 1048576" | bc -l 2>/dev/null || echo "$total_size")
        size_unit="MB"
    elif [ "$total_size" -gt 1024 ]; then
        size_display=$(echo "scale=2; $total_size / 1024" | bc -l 2>/dev/null || echo "$total_size")
        size_unit="KB"
    else
        size_display="$total_size"
        size_unit="bytes"
    fi
else
    size_display="0"
    size_unit="bytes"
fi

echo "📈 Total Objects: $total_objects"
echo "💾 Total Size: $size_display $size_unit"
echo "🔗 Bucket: s3://$BUCKET_NAME"

# List uploaded files by category
echo ""
echo "📋 Uploaded Files by Category:"
echo "==============================="

echo "🌍 Cross-Cultural Files:"
aws s3 ls "s3://$BUCKET_NAME/cross-cultural/" --profile "$AWS_PROFILE" --recursive --human-readable --summarize 2>/dev/null | grep -E "\.md$|\.csv$|\.txt$|\.json$" | head -10 || echo "  No cross-cultural files found"

echo ""
echo "🗺️  Market-Specific Files:"
aws s3 ls "s3://$BUCKET_NAME/markets/" --profile "$AWS_PROFILE" --recursive --human-readable --summarize 2>/dev/null | grep -E "\.md$|\.csv$|\.txt$|\.json$" | head -10 || echo "  No market files found"

echo ""
echo "✅ Knowledge Base Document Upload Complete!"
echo ""
echo "🔄 Next Steps:"
echo "1. Sync the knowledge base data sources in AWS Bedrock console"
echo "2. Test the cultural intelligence Lambda function"
echo "3. Update the Bedrock agent to include cultural intelligence action group"

# Optional: Trigger knowledge base sync if data sources are configured
echo ""
echo "💡 To trigger knowledge base synchronization, run:"
echo "   aws bedrock-agent start-ingestion-job --knowledge-base-id <KB_ID> --data-source-id <DATA_SOURCE_ID> --profile $AWS_PROFILE"