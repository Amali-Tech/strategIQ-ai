import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for Campaign Generation Agent - Image Analysis action group
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
        image_url = parameters.get('image_url', parameters.get('s3-path-uri', ''))
        analysis_type = parameters.get('analysis_type', 'full')
        target_market = parameters.get('target_market', 'global')
        
        logger.info(f"Processing image analysis - URL: {image_url}, Type: {analysis_type}, Market: {target_market}")
        
        # Placeholder response structure
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "image_analysis",
                "function": "analyze_image",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "success",
                                "analysis": {
                                    "image_type": "marketing_visual",
                                    "dominant_colors": ["#FF6B35", "#004E89", "#FFFFFF"],
                                    "text_detected": True,
                                    "brand_elements": ["logo", "tagline"],
                                    "visual_style": "modern_minimalist",
                                    "target_audience": "young_professionals",
                                    "cultural_sensitivity_score": 0.85,
                                    "recommendations": [
                                        "Consider adjusting color palette for better accessibility",
                                        "Text contrast meets WCAG standards",
                                        "Visual elements align with target demographic"
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
                "actionGroup": "image_analysis",
                "function": "analyze_image",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "error",
                                "message": f"Failed to analyze image: {str(e)}",
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