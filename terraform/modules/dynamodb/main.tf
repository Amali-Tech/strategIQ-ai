# Dynamodb Module
# This module manages dynamodb resources for the AWS AI Hackathon project

# Product Analysis Data Table - Stores initial image analysis results
resource "aws_dynamodb_table" "product_analysis" {
  name           = "${var.project_name}-${var.environment}-product-analysis"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "imageHash"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "imageHash"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-product-analysis"
    Purpose = "Store product image analysis results"
  })
}

# Enriched Data Table - Stores enriched product data with YouTube insights
resource "aws_dynamodb_table" "enriched_data" {
  name           = "${var.project_name}-${var.environment}-enriched-data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "imageHash"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "imageHash"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-enriched-data"
    Purpose = "Store enriched product data with YouTube insights"
  })
}

# Campaign Data Table - Stores generated campaign content
resource "aws_dynamodb_table" "campaign_data" {
  name           = "${var.project_name}-${var.environment}-campaign-data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "imageHash"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "imageHash"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-campaign-data"
    Purpose = "Store generated campaign content and strategies"
  })
}

# Comments Table - Stores comments for sentiment analysis (VOM table structure)
resource "aws_dynamodb_table" "comments" {
  name           = "vom-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK" 
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "vom-table"
    Purpose = "Store comments and sentiment analysis data"
  })
}

# Sentiment Analysis Table - Stores sentiment analysis results
resource "aws_dynamodb_table" "sentiment_analysis" {
  name           = "${var.project_name}-${var.environment}-sentiment-analysis"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "imageHash"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "imageHash"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-sentiment-analysis"
    Purpose = "Store sentiment analysis results from campaign content"
  })
}

# Action Items Table - Stores generated action items and recommendations
resource "aws_dynamodb_table" "action_items" {
  name           = "${var.project_name}-${var.environment}-action-items"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "imageHash"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "imageHash"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-action-items"
    Purpose = "Store generated action items and marketing recommendations"
  })
}
