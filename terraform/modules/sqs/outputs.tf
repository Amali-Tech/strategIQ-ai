output "image_generation_queue_arn" {
  description = "ARN of the image generation SQS queue"
  value       = aws_sqs_queue.image_generation.arn
}

output "image_generation_queue_url" {
  description = "URL of the image generation SQS queue"
  value       = aws_sqs_queue.image_generation.url
}
