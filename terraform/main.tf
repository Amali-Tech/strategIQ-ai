

module "agents" {
  source = "./modules/agents"
  
  tags = var.tags
}

module "api_gateway" {
  source = "./modules/api-gateway"
  
  supervisor_agent_id       = module.agents.supervisor_agent.agent_id
  supervisor_agent_alias_id = "TSTALIASID"
  api_stage_name           = var.environment
  
  tags = var.tags
}