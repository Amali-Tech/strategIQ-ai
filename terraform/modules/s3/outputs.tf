# S3 Module Outputs

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}

output "generated_assets_bucket_name" {
  description = "Name of the generated assets S3 bucket"
  value       = aws_s3_bucket.generated_assets.bucket
}

output "generated_assets_bucket_arn" {
  description = "ARN of the generated assets S3 bucket"
  value       = aws_s3_bucket.generated_assets.arn
}

output "generated_assets_bucket_domain_name" {
  description = "Domain name of the generated assets S3 bucket"
  value       = aws_s3_bucket.generated_assets.bucket_domain_name
}

output "generated_assets_bucket_regional_domain_name" {
  description = "Regional domain name of the generated assets S3 bucket"
  value       = aws_s3_bucket.generated_assets.bucket_regional_domain_name
}
