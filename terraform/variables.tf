# project name
variable "project_name" {
    type = string
    description = "The name of this project"
}

# default aws region
variable "aws_region" {
    type = string
    description = "The region in which these resources would be created."
}

# environment
variable "environment" {
    type = string
    description = "could be one of development, production or staging or any other name"
}
