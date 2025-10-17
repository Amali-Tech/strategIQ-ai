# Knowledge Bases Module for Cross-Cultural Marketing Intelligence
# This module creates Bedrock Knowledge Bases with S3 data sources for cultural adaptation

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Bucket for Knowledge Base Documents
resource "aws_s3_bucket" "knowledge_base_documents" {
  bucket = "${var.project_name}-${var.environment}-knowledge-base-docs"

  tags = {
    Name        = "${var.project_name}-${var.environment}-knowledge-base-docs"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Store knowledge base documents for cultural adaptation"
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "knowledge_base_documents" {
  bucket = aws_s3_bucket.knowledge_base_documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base_documents" {
  bucket = aws_s3_bucket.knowledge_base_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "knowledge_base_documents" {
  bucket = aws_s3_bucket.knowledge_base_documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for Bedrock Knowledge Base
resource "aws_iam_role" "knowledge_base_role" {
  name = "${var.project_name}-${var.environment}-knowledge-base-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-knowledge-base-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Knowledge Base S3 Access
resource "aws_iam_policy" "knowledge_base_s3_policy" {
  name        = "${var.project_name}-${var.environment}-knowledge-base-s3-policy"
  description = "Policy for Bedrock Knowledge Base to access S3 documents"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.knowledge_base_documents.arn,
          "${aws_s3_bucket.knowledge_base_documents.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-knowledge-base-s3-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Bedrock Model Access  
resource "aws_iam_policy" "knowledge_base_bedrock_policy" {
  name        = "${var.project_name}-${var.environment}-knowledge-base-bedrock-policy"
  description = "Policy for Bedrock Knowledge Base to access embedding models and OpenSearch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = [
          aws_opensearchserverless_collection.cultural_knowledge_base.arn,
          aws_opensearchserverless_collection.market_knowledge_base.arn
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-knowledge-base-bedrock-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}# Attach S3 Policy to Knowledge Base Role
resource "aws_iam_role_policy_attachment" "knowledge_base_s3_policy" {
  role       = aws_iam_role.knowledge_base_role.name
  policy_arn = aws_iam_policy.knowledge_base_s3_policy.arn
}

# Attach Bedrock Policy to Knowledge Base Role
resource "aws_iam_role_policy_attachment" "knowledge_base_bedrock_policy" {
  role       = aws_iam_role.knowledge_base_role.name
  policy_arn = aws_iam_policy.knowledge_base_bedrock_policy.arn
}

# OpenSearch Serverless Encryption Policy
resource "aws_opensearchserverless_security_policy" "knowledge_base_encryption" {
  name = "${var.project_name}-${var.environment}-kb-encryption"
  type = "encryption"
  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.project_name}-${var.environment}-cultural-kb",
          "collection/${var.project_name}-${var.environment}-market-kb"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

# OpenSearch Serverless Network Policy
resource "aws_opensearchserverless_security_policy" "knowledge_base_network" {
  name = "${var.project_name}-${var.environment}-kb-network"
  type = "network"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.project_name}-${var.environment}-cultural-kb",
            "collection/${var.project_name}-${var.environment}-market-kb"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# OpenSearch Serverless Data Access Policy
resource "aws_opensearchserverless_access_policy" "knowledge_base_data_access" {
  name = "${var.project_name}-${var.environment}-kb-data-access"
  type = "data"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.project_name}-${var.environment}-cultural-kb",
            "collection/${var.project_name}-${var.environment}-market-kb"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems", 
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.project_name}-${var.environment}-cultural-kb/*",
            "index/${var.project_name}-${var.environment}-market-kb/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
          ResourceType = "index"
        }
      ]
      Principal = [
        aws_iam_role.knowledge_base_role.arn,
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  ])
}

# OpenSearch Serverless Collection for Cultural Knowledge Base
resource "aws_opensearchserverless_collection" "cultural_knowledge_base" {
  name = "${var.project_name}-${var.environment}-cultural-kb"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.knowledge_base_encryption,
    aws_opensearchserverless_security_policy.knowledge_base_network,
    aws_opensearchserverless_access_policy.knowledge_base_data_access
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-kb"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Vector search for cross-cultural marketing intelligence"
  }
}

# OpenSearch Serverless Collection for Market Knowledge Base
resource "aws_opensearchserverless_collection" "market_knowledge_base" {
  name = "${var.project_name}-${var.environment}-market-kb"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.knowledge_base_encryption,
    aws_opensearchserverless_security_policy.knowledge_base_network,
    aws_opensearchserverless_access_policy.knowledge_base_data_access
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-market-kb"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Vector search for market-specific intelligence"
  }
}

# Bedrock Knowledge Base for Cross-Cultural Data
resource "aws_bedrockagent_knowledge_base" "cultural_intelligence" {
  name     = "${var.project_name}-${var.environment}-cultural-intelligence"
  role_arn = aws_iam_role.knowledge_base_role.arn
  description = "Cross-cultural marketing intelligence knowledge base for global campaign adaptation"

  knowledge_base_configuration {
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1"
    }
    type = "VECTOR"
  }

  storage_configuration {
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.cultural_knowledge_base.arn
      vector_index_name = "cultural-intelligence-index"
      field_mapping {
        vector_field   = "vector"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
    type = "OPENSEARCH_SERVERLESS"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cultural-intelligence"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Cross-cultural marketing intelligence"
  }
}

# Bedrock Knowledge Base for Market Data
resource "aws_bedrockagent_knowledge_base" "market_intelligence" {
  name     = "${var.project_name}-${var.environment}-market-intelligence"
  role_arn = aws_iam_role.knowledge_base_role.arn
  description = "Market-specific intelligence knowledge base for regional campaign optimization"

  knowledge_base_configuration {
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1"
    }
    type = "VECTOR"
  }

  storage_configuration {
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.market_knowledge_base.arn
      vector_index_name = "market-intelligence-index"
      field_mapping {
        vector_field   = "vector"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
    type = "OPENSEARCH_SERVERLESS"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-market-intelligence"
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Market-specific intelligence"
  }
}

# Data Source for Cultural Knowledge Base
resource "aws_bedrockagent_data_source" "cultural_data_source" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.cultural_intelligence.id
  name              = "cultural-cross-adaptation-data"
  description       = "Cross-cultural adaptation guidelines and matrices"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = aws_s3_bucket.knowledge_base_documents.arn
      inclusion_prefixes = ["cross-cultural/"]
    }
  }
}

# Data Source for Market Knowledge Base
resource "aws_bedrockagent_data_source" "market_data_source" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.market_intelligence.id
  name              = "market-specific-intelligence-data"
  description       = "Market-specific cultural guides and preferences"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = aws_s3_bucket.knowledge_base_documents.arn
      inclusion_prefixes = ["markets/"]
    }
  }
}