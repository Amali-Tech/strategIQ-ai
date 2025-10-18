import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for Campaign Generation Agent - Data Enrichment action group
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
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
        campaign_id = parameters.get('campaign_id', 'default_campaign')
        product_category = parameters.get('product_category', parameters.get('category', 'general'))
        budget_range = parameters.get('budget_range', 'medium')
        campaign_objectives = parameters.get('campaign_objectives', ['awareness'])
        target_audience = parameters.get('target_audience', {})
        
        logger.info(f"Processing data enrichment - Campaign: {campaign_id}, Category: {product_category}, Budget: {budget_range}")
        
        # Placeholder response structure
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "data_enrichment",
                "function": "enrich_campaign_data",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "success",
                                "enriched_data": {
                                    "demographic_insights": {
                                        "age_groups": {
                                            "18-24": 0.25,
                                            "25-34": 0.35,
                                            "35-44": 0.30,
                                            "45+": 0.10
                                        },
                                        "gender_distribution": {
                                            "male": 0.48,
                                            "female": 0.52
                                        },
                                        "income_brackets": {
                                            "low": 0.20,
                                            "middle": 0.60,
                                            "high": 0.20
                                        }
                                    },
                                    "behavioral_patterns": {
                                        "preferred_channels": ["social_media", "email", "mobile_apps"],
                                        "engagement_times": ["morning", "evening"],
                                        "content_preferences": ["video", "interactive", "visual"]
                                    },
                                    "market_trends": {
                                        "trending_topics": ["sustainability", "digital_transformation", "wellness"],
                                        "seasonal_factors": ["holiday_season", "back_to_school"],
                                        "competitive_landscape": "moderate_competition"
                                    },
                                    "personalization_opportunities": [
                                        "Location-based messaging",
                                        "Time-sensitive offers",
                                        "Interest-based content"
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
                "actionGroup": "data_enrichment",
                "function": "enrich_campaign_data",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "error",
                                "message": f"Failed to enrich campaign data: {str(e)}",
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