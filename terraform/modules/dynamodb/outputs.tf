output "products_table_name" {
  description = "Name of the products DynamoDB table"
  value       = aws_dynamodb_table.products.name
}

output "products_table_arn" {
  description = "ARN of the products DynamoDB table"
  value       = aws_dynamodb_table.products.arn
}

output "generated_images_table_name" {
  description = "Name of the generated images DynamoDB table"
  value       = aws_dynamodb_table.generated_images.name
}

output "generated_images_table_arn" {
  description = "ARN of the generated images DynamoDB table"
  value       = aws_dynamodb_table.generated_images.arn
}
