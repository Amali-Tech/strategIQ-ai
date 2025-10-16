import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for Lokalize Agent - Cultural Adaptation action group
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
        content = parameters.get('content', parameters.get('inputText', 'sample content'))
        target_culture = parameters.get('target_culture', parameters.get('target_market', 'global'))
        content_type = parameters.get('content_type', 'marketing')
        
        logger.info(f"Processing cultural adaptation - Content: {content[:50]}..., Culture: {target_culture}")
        
        # Placeholder response structure
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "cultural_adaptation",
                "function": "adapt_content_culturally",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "success",
                                "adaptation_results": {
                                    "original_content": "Sample marketing message",
                                    "target_culture": "japanese",
                                    "adapted_content": {
                                        "text": "Culturally adapted marketing message for Japanese market",
                                        "tone": "respectful_formal",
                                        "cultural_elements": [
                                            "honorific_language",
                                            "seasonal_references",
                                            "group_harmony_emphasis"
                                        ]
                                    },
                                    "cultural_considerations": {
                                        "color_symbolism": {
                                            "avoid": ["white_for_mourning"],
                                            "prefer": ["red_for_luck", "gold_for_prosperity"]
                                        },
                                        "communication_style": "high_context",
                                        "hierarchy_awareness": "important",
                                        "gift_giving_customs": "reciprocity_expected"
                                    },
                                    "localization_notes": [
                                        "Use formal keigo language for business context",
                                        "Consider seasonal festivals in timing",
                                        "Emphasize quality and craftsmanship",
                                        "Include group benefits over individual gains"
                                    ],
                                    "risk_assessment": {
                                        "cultural_sensitivity_score": 0.92,
                                        "potential_issues": [],
                                        "recommendations": [
                                            "Review with native Japanese speaker",
                                            "Test with focus group in target region"
                                        ]
                                    }
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
                "actionGroup": "cultural_adaptation",
                "function": "adapt_content_culturally",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "error",
                                "message": f"Failed to adapt content culturally: {str(e)}",
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