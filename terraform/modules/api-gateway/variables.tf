variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "supervisor_agent_id" {
  description = "Bedrock supervisor agent ID"
  type        = string
}

variable "supervisor_agent_alias_id" {
  description = "Bedrock supervisor agent alias ID"
  type        = string
  default     = "TSTALIASID"
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}
