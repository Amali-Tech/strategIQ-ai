# Bedrock Multi-Agent Architecture Outputs

output "bedrock_agents" {
  description = "Information about all deployed Bedrock agents"
  value = {
    campaign_generation = module.agents.campaign_generation_agent
    lokalize_agent     = module.agents.lokalize_agent
    voice_of_market    = module.agents.voice_of_market_agent
    supervisor         = module.agents.supervisor_agent
  }
}

output "action_groups" {
  description = "Information about all action groups"
  value = module.agents.action_groups
}

output "multi_agent_collaboration_setup" {
  description = "Instructions for setting up multi-agent collaboration"
  value = module.agents.multi_agent_collaboration_setup
}

output "api_gateway" {
  description = "API Gateway information"
  value = {
    api_url        = module.api_gateway.api_gateway_stage_url
    available_routes = module.api_gateway.api_routes
    intent_parser_function = module.api_gateway.intent_parser_function_name
  }
}

output "deployment_summary" {
  description = "Summary of the deployed infrastructure"
  value = {
    region = var.aws_region
    agents_deployed = 4
    lambda_functions_deployed = 7  # 6 action groups + 1 intent parser
    action_groups_deployed = 6
    api_gateway_deployed = true
    multi_agent_collaboration = "Manual setup required in AWS Bedrock console"
    api_endpoint = module.api_gateway.api_gateway_stage_url
    next_steps = [
      "1. Open AWS Bedrock console in ${var.aws_region}",
      "2. Navigate to the supervisor-agent",
      "3. Enable multi-agent collaboration",
      "4. Add the three collaborator agents",
      "5. Test API endpoints at ${module.api_gateway.api_gateway_stage_url}",
      "6. Test individual agents and collaboration"
    ]
  }
}