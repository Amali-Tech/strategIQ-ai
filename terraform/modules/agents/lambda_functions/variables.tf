variable "agent_name" {
  description = "Name of the Bedrock agent"
  type        = string
}

variable "functions" {
  description = "Map of Lambda functions to create"
  type = map(object({
    handler_path = string
    description  = string
  }))
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}