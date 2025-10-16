output "campaign_generation_agent" {
  description = "Campaign Generation Agent details"
  value = {
    agent_id           = aws_bedrockagent_agent.campaign_generation_agent.agent_id
    agent_arn          = aws_bedrockagent_agent.campaign_generation_agent.agent_arn
    agent_name         = aws_bedrockagent_agent.campaign_generation_agent.agent_name
    foundation_model   = aws_bedrockagent_agent.campaign_generation_agent.foundation_model
  }
}

output "lokalize_agent" {
  description = "Lokalize Agent (Cultural Analysis) details"
  value = {
    agent_id           = aws_bedrockagent_agent.cultural_analysis_agent.agent_id
    agent_arn          = aws_bedrockagent_agent.cultural_analysis_agent.agent_arn
    agent_name         = aws_bedrockagent_agent.cultural_analysis_agent.agent_name
    foundation_model   = aws_bedrockagent_agent.cultural_analysis_agent.foundation_model
  }
}

output "voice_of_market_agent" {
  description = "Voice of the Market Agent details"
  value = {
    agent_id           = aws_bedrockagent_agent.voice_of_the_market_agent.agent_id
    agent_arn          = aws_bedrockagent_agent.voice_of_the_market_agent.agent_arn
    agent_name         = aws_bedrockagent_agent.voice_of_the_market_agent.agent_name
    foundation_model   = aws_bedrockagent_agent.voice_of_the_market_agent.foundation_model
  }
}

output "supervisor_agent" {
  description = "Supervisor Agent details"
  value = {
    agent_id           = aws_bedrockagent_agent.supervisor_agent.agent_id
    agent_arn          = aws_bedrockagent_agent.supervisor_agent.agent_arn
    agent_name         = aws_bedrockagent_agent.supervisor_agent.agent_name
    foundation_model   = aws_bedrockagent_agent.supervisor_agent.foundation_model
    collaboration_role = "SUPERVISOR"
  }
}

output "multi_agent_collaboration_setup" {
  description = "Information for setting up multi-agent collaboration manually"
  value = {
    supervisor_agent_id = aws_bedrockagent_agent.supervisor_agent.agent_id
    supervisor_agent_name = aws_bedrockagent_agent.supervisor_agent.agent_name
    collaborator_agents = {
      campaign_generation = {
        agent_id = aws_bedrockagent_agent.campaign_generation_agent.agent_id
        agent_name = aws_bedrockagent_agent.campaign_generation_agent.agent_name
      }
      lokalize = {
        agent_id = aws_bedrockagent_agent.cultural_analysis_agent.agent_id
        agent_name = aws_bedrockagent_agent.cultural_analysis_agent.agent_name
      }
      voice_of_market = {
        agent_id = aws_bedrockagent_agent.voice_of_the_market_agent.agent_id
        agent_name = aws_bedrockagent_agent.voice_of_the_market_agent.agent_name
      }
    }
    manual_setup_instructions = "After deployment, configure multi-agent collaboration in the AWS Bedrock console by enabling collaboration on the supervisor agent and adding the three collaborator agents."
  }
}

output "action_groups" {
  description = "Action groups created for each agent"
  value = {
    campaign_generation = {
      image_analysis = {
        action_group_id = aws_bedrockagent_agent_action_group.campaign_generation_image_analysis.action_group_id
        lambda_arn = module.campaign_generation_lambdas.lambda_functions["image_analysis"].arn
      }
      data_enrichment = {
        action_group_id = aws_bedrockagent_agent_action_group.campaign_generation_data_enrichment.action_group_id
        lambda_arn = module.campaign_generation_lambdas.lambda_functions["data_enrichment"].arn
      }
    }
    lokalize_agent = {
      cultural_adaptation = {
        action_group_id = aws_bedrockagent_agent_action_group.lokalize_cultural_adaptation.action_group_id
        lambda_arn = module.lokalize_agent_lambdas.lambda_functions["cultural_adaptation"].arn
      }
      language_translation = {
        action_group_id = aws_bedrockagent_agent_action_group.lokalize_language_translation.action_group_id
        lambda_arn = module.lokalize_agent_lambdas.lambda_functions["language_translation"].arn
      }
    }
    voice_of_market = {
      market_analysis = {
        action_group_id = aws_bedrockagent_agent_action_group.voice_of_market_market_analysis.action_group_id
        lambda_arn = module.voice_of_market_lambdas.lambda_functions["market_analysis"].arn
      }
      sentiment_analysis = {
        action_group_id = aws_bedrockagent_agent_action_group.voice_of_market_sentiment_analysis.action_group_id
        lambda_arn = module.voice_of_market_lambdas.lambda_functions["sentiment_analysis"].arn
      }
    }
  }
}