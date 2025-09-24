# IAM Module Outputs

output "lambda_image_analysis_role_arn" {
  description = "ARN of the Lambda image analysis execution role"
  value       = aws_iam_role.lambda_image_analysis_role.arn
}

output "lambda_campaign_role_arn" {
  description = "ARN of the Lambda campaign execution role"
  value       = aws_iam_role.lambda_campaign_role.arn
}

output "lambda_api_role_arn" {
  description = "ARN of the Lambda API execution role"
  value       = aws_iam_role.lambda_api_role.arn
}

output "eventbridge_pipes_role_arn" {
  description = "ARN of the EventBridge Pipes execution role"
  value       = aws_iam_role.eventbridge_pipes_role.arn
}

output "all_lambda_role_arns" {
  description = "Map of all Lambda role ARNs"
  value = {
    image_analysis = aws_iam_role.lambda_image_analysis_role.arn
    campaign       = aws_iam_role.lambda_campaign_role.arn
    api           = aws_iam_role.lambda_api_role.arn
  }
}
