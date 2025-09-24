# EventBridge Module Outputs

output "analysis_to_enrichment_pipe_arn" {
  description = "ARN of the analysis to enrichment EventBridge pipe"
  value       = aws_pipes_pipe.analysis_to_enrichment.arn
}

output "enriched_to_campaign_pipe_arn" {
  description = "ARN of the enriched to campaign EventBridge pipe"
  value       = aws_pipes_pipe.enriched_to_campaign.arn
}

output "campaign_to_sentiment_pipe_arn" {
  description = "ARN of the campaign to sentiment EventBridge pipe"
  value       = aws_pipes_pipe.campaign_to_sentiment.arn
}

output "campaign_sqs_trigger_uuid" {
  description = "UUID of the SQS event source mapping for campaign generator"
  value       = aws_lambda_event_source_mapping.campaign_sqs_trigger.uuid
}

output "all_pipe_arns" {
  description = "Map of all EventBridge pipe ARNs"
  value = {
    analysis_to_enrichment = aws_pipes_pipe.analysis_to_enrichment.arn
    enriched_to_campaign  = aws_pipes_pipe.enriched_to_campaign.arn
    campaign_to_sentiment = aws_pipes_pipe.campaign_to_sentiment.arn
  }
}

# TODO: Add module outputs here
