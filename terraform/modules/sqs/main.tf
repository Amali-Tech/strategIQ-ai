resource "aws_sqs_queue" "image_generation" {
  name                      = var.image_generation_queue_name
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400
  delay_seconds              = 0
  receive_wait_time_seconds  = 0
  # Not a FIFO queue
}

resource "aws_lambda_event_source_mapping" "generate_images" {
  event_source_arn = aws_sqs_queue.image_generation.arn
  function_name    = var.generate_images_lambda_arn
  enabled          = true
  batch_size       = 1
}
