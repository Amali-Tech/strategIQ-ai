# SQS Module Outputs

# Campaign Generation Queue
output "campaign_generation_queue_url" {
  description = "URL of the campaign generation SQS queue"
  value       = aws_sqs_queue.campaign_generation.url
}

output "campaign_generation_queue_arn" {
  description = "ARN of the campaign generation SQS queue"
  value       = aws_sqs_queue.campaign_generation.arn
}

output "campaign_generation_queue_name" {
  description = "Name of the campaign generation SQS queue"
  value       = aws_sqs_queue.campaign_generation.name
}

# Dead Letter Queue
output "campaign_generation_dlq_url" {
  description = "URL of the campaign generation dead letter queue"
  value       = aws_sqs_queue.campaign_generation_dlq.url
}

output "campaign_generation_dlq_arn" {
  description = "ARN of the campaign generation dead letter queue"
  value       = aws_sqs_queue.campaign_generation_dlq.arn
}

output "campaign_generation_dlq_name" {
  description = "Name of the campaign generation dead letter queue"
  value       = aws_sqs_queue.campaign_generation_dlq.name
}

# Consolidated outputs for easier consumption
output "queue_urls" {
  description = "Map of all SQS queue URLs"
  value = {
    campaign_generation = aws_sqs_queue.campaign_generation.url
    campaign_generation_dlq = aws_sqs_queue.campaign_generation_dlq.url
  }
}

output "queue_arns" {
  description = "List of all SQS queue ARNs"
  value = [
    aws_sqs_queue.campaign_generation.arn,
    aws_sqs_queue.campaign_generation_dlq.arn
  ]
}

# TODO: Add module outputs here
