# SQS Module
# This module manages sqs resources for the AWS AI Hackathon project

# Dead Letter Queue for failed campaign generation messages
resource "aws_sqs_queue" "campaign_generation_dlq" {
  name = "${var.project_name}-${var.environment}-campaign-generation-dlq"
  
  message_retention_seconds = 1209600  # 14 days
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-campaign-generation-dlq"
    Purpose = "Dead letter queue for failed campaign generation messages"
  })
}

# Main SQS Queue for Campaign Generation
resource "aws_sqs_queue" "campaign_generation" {
  name = "${var.project_name}-${var.environment}-campaign-generation"
  
  # Message configuration
  visibility_timeout_seconds = 900  # 15 minutes (Lambda timeout is 10 minutes)
  message_retention_seconds  = 1209600  # 14 days
  max_message_size          = 262144  # 256 KB
  delay_seconds             = 0
  receive_wait_time_seconds = 20  # Long polling
  
  # Dead letter queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.campaign_generation_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-campaign-generation"
    Purpose = "Queue for triggering campaign generation from enriched data"
  })
}

# SQS Queue Policy to allow EventBridge to send messages
resource "aws_sqs_queue_policy" "campaign_generation_policy" {
  queue_url = aws_sqs_queue.campaign_generation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgeToSendMessages"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.campaign_generation.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AllowEventBridgePipesToSendMessages"
        Effect = "Allow"
        Principal = {
          Service = "pipes.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.campaign_generation.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}
# This module manages sqs resources for the AWS AI Hackathon project

# TODO: Add your sqs resources here
