# Campaign Tracking Module
# This module manages campaign status tracking and event-driven visual asset generation

# DynamoDB table for campaign status tracking
resource "aws_dynamodb_table" "campaign_status" {
  name           = "${var.project_name}-${var.environment}-campaign-status"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "campaign_id"

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying by status
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Track campaign generation status and progress"
  }
}

# SQS Queue for visual asset generation requests
resource "aws_sqs_queue" "visual_asset_generation" {
  name                       = "${var.project_name}-${var.environment}-visual-asset-generation"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 900      # 15 minutes for processing

  # Dead letter queue for failed messages
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.visual_asset_generation_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Queue for async visual asset generation requests"
  }
}

# Dead letter queue for failed visual asset generation
resource "aws_sqs_queue" "visual_asset_generation_dlq" {
  name                       = "${var.project_name}-${var.environment}-visual-asset-generation-dlq"
  message_retention_seconds  = 1209600  # 14 days

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Dead letter queue for failed visual asset generation"
  }
}

# EventBridge custom bus for campaign events
resource "aws_cloudwatch_event_bus" "campaign_events" {
  name = "${var.project_name}-${var.environment}-campaign-events"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Custom event bus for campaign lifecycle events"
  }
}

# EventBridge rule for campaign completion events
resource "aws_cloudwatch_event_rule" "campaign_completed" {
  name           = "${var.project_name}-${var.environment}-campaign-completed"
  event_bus_name = aws_cloudwatch_event_bus.campaign_events.name
  description    = "Trigger visual asset generation when campaign analysis completes"

  event_pattern = jsonencode({
    source      = ["degenerals.campaign"]
    detail-type = ["Campaign Analysis Completed"]
    detail = {
      status = ["completed"]
    }
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Trigger visual asset generation"
  }
}

# EventBridge target to send campaign completion to SQS
resource "aws_cloudwatch_event_target" "campaign_to_sqs" {
  rule           = aws_cloudwatch_event_rule.campaign_completed.name
  event_bus_name = aws_cloudwatch_event_bus.campaign_events.name
  target_id      = "SendToVisualAssetQueue"
  arn            = aws_sqs_queue.visual_asset_generation.arn
}

# IAM policy for EventBridge to send messages to SQS
resource "aws_sqs_queue_policy" "visual_asset_generation_policy" {
  queue_url = aws_sqs_queue.visual_asset_generation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.visual_asset_generation.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# IAM policy for Lambda functions to access campaign tracking resources
resource "aws_iam_policy" "campaign_tracking_policy" {
  name        = "${var.project_name}-${var.environment}-campaign-tracking-policy"
  description = "Policy for Lambda functions to access campaign tracking resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.campaign_status.arn,
          "${aws_dynamodb_table.campaign_status.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = aws_cloudwatch_event_bus.campaign_events.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.visual_asset_generation.arn,
          aws_sqs_queue.visual_asset_generation_dlq.arn
        ]
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Access policy for campaign tracking resources"
  }
}