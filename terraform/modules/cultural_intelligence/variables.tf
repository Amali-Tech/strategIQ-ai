variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The deployment environment"
  type        = string
}

variable "cultural_intelligence_kb_id" {
  description = "ID of the Cultural Intelligence Knowledge Base"
  type        = string
  default     = ""
}

variable "cultural_intelligence_kb_arn" {
  description = "ARN of the Cultural Intelligence Knowledge Base"
  type        = string
  default     = ""
}

variable "market_intelligence_kb_id" {
  description = "ID of the Market Intelligence Knowledge Base"
  type        = string
  default     = ""
}

variable "market_intelligence_kb_arn" {
  description = "ARN of the Market Intelligence Knowledge Base"
  type        = string
  default     = ""
}

variable "s3_knowledge_base_bucket_name" {
  description = "Name of the S3 bucket containing knowledge base documents"
  type        = string
}