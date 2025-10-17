output "knowledge_base_documents_bucket_name" {
  description = "Name of the S3 bucket storing knowledge base documents"
  value       = aws_s3_bucket.knowledge_base_documents.bucket
}

output "knowledge_base_documents_bucket_arn" {
  description = "ARN of the S3 bucket storing knowledge base documents"
  value       = aws_s3_bucket.knowledge_base_documents.arn
}

output "cultural_intelligence_kb_id" {
  description = "ID of the Cultural Intelligence Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.cultural_intelligence.id
}

output "cultural_intelligence_kb_arn" {
  description = "ARN of the Cultural Intelligence Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.cultural_intelligence.arn
}

output "market_intelligence_kb_id" {
  description = "ID of the Market Intelligence Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.market_intelligence.id
}

output "market_intelligence_kb_arn" {
  description = "ARN of the Market Intelligence Knowledge Base"
  value       = aws_bedrockagent_knowledge_base.market_intelligence.arn
}

output "cultural_data_source_id" {
  description = "ID of the Cultural Data Source"
  value       = aws_bedrockagent_data_source.cultural_data_source.data_source_id
}

output "market_data_source_id" {
  description = "ID of the Market Data Source"
  value       = aws_bedrockagent_data_source.market_data_source.data_source_id
}

output "knowledge_base_role_arn" {
  description = "ARN of the Knowledge Base IAM role"
  value       = aws_iam_role.knowledge_base_role.arn
}