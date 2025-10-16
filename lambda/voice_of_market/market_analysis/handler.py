import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for Voice of the Market Agent - Market Analysis action group
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters from Bedrock agent event format
        parameters = {}
        
        # Bedrock agents pass parameters in different formats - handle all cases
        if 'parameters' in event:
            parameters = event['parameters']
            logger.info(f"Found parameters in event['parameters']: {parameters}")
        elif 'inputText' in event:
            parameters = {'inputText': event['inputText']}
            logger.info(f"Found inputText in event: {event['inputText']}")
        elif 'requestBody' in event:
            if 'content' in event['requestBody']:
                for content_type, content_data in event['requestBody']['content'].items():
                    if 'properties' in content_data:
                        parameters = content_data['properties']
                        logger.info(f"Found parameters in requestBody content: {parameters}")
                        break
        elif 'apiPath' in event and 'httpMethod' in event:
            # API Gateway format
            if event.get('body'):
                try:
                    parameters = json.loads(event['body'])
                    logger.info(f"Parsed parameters from body: {parameters}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse body as JSON: {event['body']}")
        
        # Log what we extracted
        logger.info(f"Final extracted parameters: {parameters}")
        
        # Extract specific parameters with defaults
        market_parameters = parameters.get('market_parameters', {})
        analysis_focus = parameters.get('analysis_focus', ['market_size', 'competitive_analysis'])
        time_horizon = parameters.get('time_horizon', '1_year')
        
        logger.info(f"Processing market analysis - Parameters: {market_parameters}, Focus: {analysis_focus}, Horizon: {time_horizon}")
        
        # Placeholder response structure
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "market_analysis",
                "function": "analyze_market_trends",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "success",
                                "market_analysis": {
                                    "market_overview": {
                                        "market_size": "$2.5B",
                                        "growth_rate": "12.5%",
                                        "market_maturity": "growth_stage",
                                        "key_drivers": [
                                            "digital_transformation",
                                            "remote_work_adoption",
                                            "sustainability_focus"
                                        ]
                                    },
                                    "competitive_landscape": {
                                        "market_concentration": "fragmented",
                                        "top_competitors": [
                                            {
                                                "name": "Competitor A",
                                                "market_share": "15%",
                                                "strengths": ["brand_recognition", "distribution"],
                                                "weaknesses": ["pricing", "innovation"]
                                            },
                                            {
                                                "name": "Competitor B",
                                                "market_share": "12%",
                                                "strengths": ["technology", "customer_service"],
                                                "weaknesses": ["market_reach", "brand_awareness"]
                                            }
                                        ],
                                        "competitive_intensity": "high",
                                        "barriers_to_entry": "moderate"
                                    },
                                    "consumer_insights": {
                                        "primary_segments": [
                                            {
                                                "segment": "tech_early_adopters",
                                                "size": "25%",
                                                "characteristics": ["high_income", "urban", "tech_savvy"],
                                                "pain_points": ["complexity", "integration_challenges"],
                                                "preferences": ["cutting_edge_features", "seamless_experience"]
                                            },
                                            {
                                                "segment": "cost_conscious_buyers",
                                                "size": "40%",
                                                "characteristics": ["price_sensitive", "value_focused"],
                                                "pain_points": ["high_costs", "hidden_fees"],
                                                "preferences": ["transparent_pricing", "proven_roi"]
                                            }
                                        ],
                                        "buying_behavior": {
                                            "decision_timeline": "3-6_months",
                                            "key_influencers": ["peer_reviews", "expert_opinions", "trial_experience"],
                                            "purchase_channels": ["online", "direct_sales", "partner_channels"]
                                        }
                                    },
                                    "market_trends": {
                                        "emerging_trends": [
                                            {
                                                "trend": "ai_integration",
                                                "impact": "high",
                                                "timeline": "12-18_months",
                                                "description": "Increasing demand for AI-powered solutions"
                                            },
                                            {
                                                "trend": "sustainability_focus",
                                                "impact": "medium",
                                                "timeline": "6-12_months",
                                                "description": "Growing emphasis on environmental responsibility"
                                            }
                                        ],
                                        "declining_trends": [
                                            "legacy_system_preference",
                                            "on_premise_only_solutions"
                                        ]
                                    },
                                    "opportunities": [
                                        "Underserved SMB market segment",
                                        "Integration with popular platforms",
                                        "Sustainability-focused messaging",
                                        "Mobile-first user experience"
                                    ],
                                    "threats": [
                                        "Economic downturn impact",
                                        "Regulatory changes",
                                        "New market entrants",
                                        "Technology disruption"
                                    ]
                                }
                            })
                        }
                    }
                }
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Full event for debugging: {json.dumps(event, default=str)}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "market_analysis",
                "function": "analyze_market_trends",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "error",
                                "message": f"Failed to analyze market trends: {str(e)}",
                                "debug_info": {
                                    "event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict",
                                    "context_info": str(context)
                                }
                            })
                        }
                    }
                }
            }
        }