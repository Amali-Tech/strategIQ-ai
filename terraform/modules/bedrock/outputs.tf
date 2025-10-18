# Bedrock Module Outputs

output "supervisor_agent_id" {
  description = "ID of the supervisor Bedrock agent"
  value       = aws_bedrockagent_agent.supervisor.agent_id
}

output "supervisor_agent_arn" {
  description = "ARN of the supervisor Bedrock agent"
  value       = aws_bedrockagent_agent.supervisor.agent_arn
}

output "supervisor_agent_alias_id" {
  description = "Alias ID of the supervisor Bedrock agent"
  value       = length(aws_bedrockagent_agent_alias.supervisor_alias) > 0 ? aws_bedrockagent_agent_alias.supervisor_alias[0].agent_alias_id : null
}

output "supervisor_agent_alias_arn" {
  description = "ARN of the supervisor Bedrock agent alias"
  value       = length(aws_bedrockagent_agent_alias.supervisor_alias) > 0 ? aws_bedrockagent_agent_alias.supervisor_alias[0].agent_alias_arn : null
}

output "bedrock_agent_role_arn" {
  description = "ARN of the Bedrock agent IAM role"
  value       = aws_iam_role.bedrock_agent_role.arn
}