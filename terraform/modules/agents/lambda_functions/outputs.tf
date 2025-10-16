output "lambda_functions" {
  description = "Map of created Lambda functions"
  value = {
    for k, v in aws_lambda_function.action_group_lambda : k => {
      arn           = v.arn
      function_name = v.function_name
      invoke_arn    = v.invoke_arn
    }
  }
}

output "lambda_roles" {
  description = "Map of Lambda execution roles"
  value = {
    for k, v in aws_iam_role.lambda_execution_role : k => {
      arn  = v.arn
      name = v.name
    }
  }
}