# Dynamodb Module Outputs

# Table Names
output "product_analysis_table_name" {
  description = "Name of the product analysis DynamoDB table"
  value       = aws_dynamodb_table.product_analysis.name
}

output "enriched_data_table_name" {
  description = "Name of the enriched data DynamoDB table"
  value       = aws_dynamodb_table.enriched_data.name
}

output "campaign_data_table_name" {
  description = "Name of the campaign data DynamoDB table"
  value       = aws_dynamodb_table.campaign_data.name
}

output "comments_table_name" {
  description = "Name of the comments DynamoDB table"
  value       = aws_dynamodb_table.comments.name
}

output "sentiment_analysis_table_name" {
  description = "Name of the sentiment analysis DynamoDB table"
  value       = aws_dynamodb_table.sentiment_analysis.name
}

output "action_items_table_name" {
  description = "Name of the action items DynamoDB table"
  value       = aws_dynamodb_table.action_items.name
}

# Table ARNs
output "product_analysis_table_arn" {
  description = "ARN of the product analysis DynamoDB table"
  value       = aws_dynamodb_table.product_analysis.arn
}

output "enriched_data_table_arn" {
  description = "ARN of the enriched data DynamoDB table"
  value       = aws_dynamodb_table.enriched_data.arn
}

output "campaign_data_table_arn" {
  description = "ARN of the campaign data DynamoDB table"
  value       = aws_dynamodb_table.campaign_data.arn
}

output "sentiment_analysis_table_arn" {
  description = "ARN of the sentiment analysis DynamoDB table"
  value       = aws_dynamodb_table.sentiment_analysis.arn
}

output "action_items_table_arn" {
  description = "ARN of the action items DynamoDB table"
  value       = aws_dynamodb_table.action_items.arn
}

# Stream ARNs
output "product_analysis_stream_arn" {
  description = "ARN of the product analysis DynamoDB stream"
  value       = aws_dynamodb_table.product_analysis.stream_arn
}

output "enriched_data_stream_arn" {
  description = "ARN of the enriched data DynamoDB stream"
  value       = aws_dynamodb_table.enriched_data.stream_arn
}

output "campaign_data_stream_arn" {
  description = "ARN of the campaign data DynamoDB stream"
  value       = aws_dynamodb_table.campaign_data.stream_arn
}

output "sentiment_analysis_stream_arn" {
  description = "ARN of the sentiment analysis DynamoDB stream"
  value       = aws_dynamodb_table.sentiment_analysis.stream_arn
}

output "action_items_stream_arn" {
  description = "ARN of the action items DynamoDB stream"
  value       = aws_dynamodb_table.action_items.stream_arn
}

# Consolidated outputs for easier consumption by other modules
output "table_names" {
  description = "Map of all DynamoDB table names"
  value = {
    product_analysis  = aws_dynamodb_table.product_analysis.name
    enriched_data    = aws_dynamodb_table.enriched_data.name
    campaign_data    = aws_dynamodb_table.campaign_data.name
    sentiment_analysis = aws_dynamodb_table.sentiment_analysis.name
    action_items     = aws_dynamodb_table.action_items.name
  }
}

output "table_arns" {
  description = "List of all DynamoDB table ARNs"
  value = [
    aws_dynamodb_table.product_analysis.arn,
    aws_dynamodb_table.enriched_data.arn,
    aws_dynamodb_table.campaign_data.arn,
    aws_dynamodb_table.sentiment_analysis.arn,
    aws_dynamodb_table.action_items.arn
  ]
}

output "stream_arns" {
  description = "List of all DynamoDB stream ARNs"
  value = [
    aws_dynamodb_table.product_analysis.stream_arn,
    aws_dynamodb_table.enriched_data.stream_arn,
    aws_dynamodb_table.campaign_data.stream_arn,
    aws_dynamodb_table.sentiment_analysis.stream_arn,
    aws_dynamodb_table.action_items.stream_arn
  ]
}
