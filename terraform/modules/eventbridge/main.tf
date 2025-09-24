# EventBridge Module
# This module manages EventBridge resources for the AWS AI Hackathon project

# EventBridge Pipe: Product Analysis DynamoDB Stream -> Enrichment Lambda
resource "aws_pipes_pipe" "analysis_to_enrichment" {
  name     = "${var.project_name}-${var.environment}-analysis-to-enrichment"
  role_arn = var.eventbridge_pipes_role_arn
  
  source = var.product_analysis_stream_arn
  target = var.enrichment_lambda_arn
  
  source_parameters {
    dynamodb_stream_parameters {
      starting_position = "LATEST"
      batch_size        = 1
      maximum_batching_window_in_seconds = 5
    }
    
    filter_criteria {
      filter {
        pattern = jsonencode({
          eventName = ["INSERT", "MODIFY"]
        })
      }
    }
  }
  
  target_parameters {
  }
  
  tags = var.tags
}

# EventBridge Pipe: Enriched Data DynamoDB Stream -> Campaign Generation SQS
resource "aws_pipes_pipe" "enriched_to_campaign" {
  name     = "${var.project_name}-${var.environment}-enriched-to-campaign"
  role_arn = var.eventbridge_pipes_role_arn
  
  source = var.enriched_data_stream_arn
  target = var.campaign_sqs_queue_arn
  
  source_parameters {
    dynamodb_stream_parameters {
      starting_position = "LATEST"
      batch_size        = 1
      maximum_batching_window_in_seconds = 5
    }
    
    filter_criteria {
      filter {
        pattern = jsonencode({
          eventName = ["INSERT", "MODIFY"]
          dynamodb = {
            NewImage = {
              pipeline_status = {
                S = ["enriched"]
              }
            }
          }
        })
      }
    }
  }
  
  # No target_parameters needed for SQS targets in EventBridge Pipes
  
  tags = var.tags
}

# EventBridge Pipe: Campaign Data DynamoDB Stream -> Sentiment Analysis Lambda
resource "aws_pipes_pipe" "campaign_to_sentiment" {
  name     = "${var.project_name}-${var.environment}-campaign-to-sentiment"
  role_arn = var.eventbridge_pipes_role_arn
  
  source = var.campaign_data_stream_arn
  target = var.campaign_generator_lambda_arn
  
  source_parameters {
    dynamodb_stream_parameters {
      starting_position = "LATEST"
      batch_size        = 1
      maximum_batching_window_in_seconds = 5
    }
    
    filter_criteria {
      filter {
        pattern = jsonencode({
          eventName = ["INSERT", "MODIFY"]
          dynamodb = {
            NewImage = {
              pipeline_status = {
                S = ["campaign_generated"]
              }
            }
          }
        })
      }
    }
  }
  
  # No target_parameters needed for Lambda targets in EventBridge Pipes
  
  tags = var.tags
}

# SQS Event Source Mapping for Campaign Generator Lambda
resource "aws_lambda_event_source_mapping" "campaign_sqs_trigger" {
  event_source_arn = var.campaign_sqs_queue_arn
  function_name    = var.campaign_generator_lambda_name
  batch_size       = 1
  
  depends_on = [aws_pipes_pipe.enriched_to_campaign]
}
