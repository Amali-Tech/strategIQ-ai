variable "products_table_name" {
  description = "Name of the DynamoDB table for products and analysis records"
  type        = string
  default     = "products"
}

variable "generated_images_table_name" {
  description = "Name of the DynamoDB table for generated image metadata and status"
  type        = string
  default     = "generated_images"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for tagging resources"
  type        = string
}
