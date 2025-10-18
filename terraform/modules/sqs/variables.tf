variable "image_generation_queue_name" {
  description = "Name of the SQS queue for image generation requests"
  type        = string
  default     = "image-generation-queue"
}

variable "generate_images_lambda_arn" {
  description = "ARN of the generate-images Lambda function to trigger from SQS"
  type        = string
}
