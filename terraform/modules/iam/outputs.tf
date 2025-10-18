# Iam Module Outputs

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.name
}

output "s3_upload_policy_arn" {
  description = "ARN of the S3 upload policy"
  value       = aws_iam_policy.s3_upload_policy.arn
}
