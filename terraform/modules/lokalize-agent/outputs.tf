# Lokalize Agent Module Outputs

output "agent_id" {
  description = "ID of the Bedrock Agent"
  value       = aws_cloudformation_stack.lokalize_agent.outputs["AgentId"]
}

output "agent_arn" {
  description = "ARN of the Bedrock Agent"
  value       = aws_cloudformation_stack.lokalize_agent.outputs["AgentArn"]
}

output "agent_alias_id" {
  description = "ID of the Bedrock Agent Alias"
  value       = aws_cloudformation_stack.lokalize_agent.outputs["AgentAliasId"]
}

output "agent_alias_arn" {
  description = "ARN of the Bedrock Agent Alias"
  value       = aws_cloudformation_stack.lokalize_agent.outputs["AgentAliasArn"]
}

output "lambda_functions" {
  description = "Map of Lambda function names and ARNs"
  value = {
    cultural_analysis    = aws_lambda_function.cultural_analysis.function_name
    translation         = aws_lambda_function.translation.function_name
    content_regeneration = aws_lambda_function.content_regeneration.function_name
  }
}

output "lambda_function_arns" {
  description = "Map of Lambda function ARNs"
  value = {
    cultural_analysis    = aws_lambda_function.cultural_analysis.arn
    translation         = aws_lambda_function.translation.arn
    content_regeneration = aws_lambda_function.content_regeneration.arn
  }
}