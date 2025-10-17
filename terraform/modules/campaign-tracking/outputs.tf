output "campaign_status_table_name" {
  value       = aws_dynamodb_table.campaign_status.name
  description = "Name of the campaign status DynamoDB table"
}

output "campaign_status_table_arn" {
  value       = aws_dynamodb_table.campaign_status.arn
  description = "ARN of the campaign status DynamoDB table"
}

output "visual_asset_queue_url" {
  value       = aws_sqs_queue.visual_asset_generation.url
  description = "URL of the visual asset generation SQS queue"
}

output "visual_asset_queue_arn" {
  value       = aws_sqs_queue.visual_asset_generation.arn
  description = "ARN of the visual asset generation SQS queue"
}

output "campaign_events_bus_name" {
  value       = aws_cloudwatch_event_bus.campaign_events.name
  description = "Name of the campaign events EventBridge bus"
}

output "campaign_events_bus_arn" {
  value       = aws_cloudwatch_event_bus.campaign_events.arn
  description = "ARN of the campaign events EventBridge bus"
}

output "campaign_tracking_policy_arn" {
  value       = aws_iam_policy.campaign_tracking_policy.arn
  description = "ARN of the campaign tracking IAM policy"
}