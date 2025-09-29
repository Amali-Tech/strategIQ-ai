# S3 Module
# This module manages s3 resources for the AWS AI Hackathon project

# S3 Bucket for storing product images
resource "aws_s3_bucket" "product_images" {
  bucket = "${var.project_name}-${var.environment}-product-images-${random_string.bucket_suffix.result}"
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-product-images"
    Purpose = "Store product images for analysis and processing"
  })
  force_destroy = true
}

# Random string for unique bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Public Access Block - Allow public reads
resource "aws_s3_bucket_public_access_block" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 Bucket Policy - Allow public read access and Rekognition access
resource "aws_s3_bucket_policy" "product_images_public_read" {
  bucket = aws_s3_bucket.product_images.id
  depends_on = [aws_s3_bucket_public_access_block.product_images]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource  = "${aws_s3_bucket.product_images.arn}/*"
      },
      {
        Sid = "AllowRekognitionAccess"
        Effect = "Allow"
        Principal = {
          Service = "rekognition.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:GetObjectAcl",
          "s3:GetObjectTagging",
          "s3:GetObjectVersion",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.product_images.arn}/*",
          "${aws_s3_bucket.product_images.arn}"
        ]
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# S3 Bucket Versioning
# resource "aws_s3_bucket_versioning" "product_images" {
#   bucket = aws_s3_bucket.product_images.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# S3 Bucket Server Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket CORS Configuration for web uploads
resource "aws_s3_bucket_cors_configuration" "product_images" {
  bucket = aws_s3_bucket.product_images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag", "x-amz-version-id"]
    max_age_seconds = 86400
  }
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}

# S3 Bucket Lifecycle Configuration
# resource "aws_s3_bucket_lifecycle_configuration" "product_images" {
#   bucket = aws_s3_bucket.product_images.id

#   rule {
#     id     = "transition_to_ia"
#     status = "Enabled"

#     transition {
#       days          = 30
#       storage_class = "STANDARD_IA"
#     }

#     transition {
#       days          = 90
#       storage_class = "GLACIER"
#     }

#     expiration {
#       days = 365
#     }
#   }

#   rule {
#     id     = "delete_incomplete_multipart_uploads"
#     status = "Enabled"

#     abort_incomplete_multipart_upload {
#       days_after_initiation = 7
#     }
#   }
# }
