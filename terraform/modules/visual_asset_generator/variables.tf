variable "aws_region" {
  description = "AWS Region"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "s3_assets_bucket" {
  description = "S3 bucket for storing generated assets"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for storing metadata"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}