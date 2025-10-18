resource "aws_dynamodb_table" "products" {
  name           = var.products_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "product_id"
  range_key      = "user_id"

  attribute {
    name = "product_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Stores product and analysis records"
  }
}

resource "aws_dynamodb_table" "generated_images" {
  name           = var.generated_images_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Stores generated image metadata and status"
  }
}
