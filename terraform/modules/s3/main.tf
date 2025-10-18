# S3 Module
# This module manages s3 resources for the AWS AI Hackathon project

resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${var.environment}-images"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Image storage for campaign generation"
  }
}

resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "delete_after_days"
    status = "Enabled"

    filter {}

    expiration {
      days = var.days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.days
    }
  }
}

resource "aws_s3_bucket" "generated_assets" {
  bucket = "${var.project_name}-${var.environment}-generated-assets"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "Generated assets storage for campaign generation"
  }
}

resource "aws_s3_bucket_cors_configuration" "generated_assets" {
  bucket = aws_s3_bucket.generated_assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "generated_assets" {
  bucket = aws_s3_bucket.generated_assets.id

  rule {
    id     = "delete_after_days"
    status = "Enabled"

    filter {}

    expiration {
      days = var.days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.days
    }
  }
}
