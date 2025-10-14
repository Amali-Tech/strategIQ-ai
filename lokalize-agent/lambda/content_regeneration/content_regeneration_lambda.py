# lambda/content_regeneration/content_regeneration_lambda.py
import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Content regeneration Lambda for Bedrock Agents"""

    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Extract parameters from Bedrock Agent event
        if 'requestBody' in event and 'content' in event['requestBody']:
            content = event['requestBody']['content']
            if isinstance(content, dict):
                original_content = content.get('original_content', '')
                target_locale = content.get('target_locale', '')
                adaptation_level = content.get('adaptation_level', 'moderate')
                brand_voice = content.get('brand_voice', '')
                content_type = content.get('content_type', 'full_ad')
            else:
                params = json.loads(content) if isinstance(content, str) else content
                original_content = params.get('original_content', '')
                target_locale = params.get('target_locale', '')
                adaptation_level = params.get('adaptation_level', 'moderate')
                brand_voice = params.get('brand_voice', '')
                content_type = params.get('content_type', 'full_ad')
        else:
            body = event.get('body', '{}')
            if isinstance(body, str):
                params = json.loads(body)
            else:
                params = body

            original_content = params.get('original_content', '')
            target_locale = params.get('target_locale', '')
            adaptation_level = params.get('adaptation_level', 'moderate')
            brand_voice = params.get('brand_voice', '')
            content_type = params.get('content_type', 'full_ad')

        logger.info(f"Regenerating content for {target_locale}, level: {adaptation_level}")

        # Perform regeneration
        regeneration_result = regenerate_content_with_nova(
            original_content, target_locale, adaptation_level, brand_voice, content_type
        )

        # Return in Bedrock Agent format
        bedrock_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'ContentRegeneration'),
                "apiPath": event.get('apiPath', '/regenerate'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(regeneration_result)
                    }
                }
            }
        }

        logger.info("Content regeneration completed successfully")
        return bedrock_response

    except Exception as e:
        logger.error(f"Error in content regeneration: {str(e)}")

        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'ContentRegeneration'),
                "apiPath": event.get('apiPath', '/regenerate'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({
                            "error": str(e),
                            "regenerated_content": "Content regeneration failed due to technical error",
                            "adaptations_made": [],
                            "cultural_improvements": [],
                            "brand_consistency_score": 0.0
                        })
                    }
                }
            }
        }

        return error_response


def regenerate_content_with_nova(
        original_content: str,
        target_locale: str,
        adaptation_level: str,
        brand_voice: str,
        content_type: str
) -> dict:
    """Regenerate content using Amazon Nova Pro"""

    if not original_content or not target_locale:
        return {
            "regenerated_content": "Unable to regenerate: missing original content or target locale",
            "adaptations_made": [],
            "cultural_improvements": ["Provide complete original content and target locale"],
            "brand_consistency_score": 0.0
        }

    bedrock_runtime = boto3.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'

    regeneration_prompt = f"""You are an expert marketing localization specialist. Regenerate this {content_type} for {target_locale} with {adaptation_level} adaptation level.

ORIGINAL CONTENT:
{original_content}

TARGET LOCALE: {target_locale}
ADAPTATION LEVEL: {adaptation_level}
BRAND VOICE: {brand_voice if brand_voice else "Maintain original brand voice"}

Create a culturally-optimized version that:
1. Respects {target_locale} cultural values and communication styles
2. Avoids cultural taboos and sensitivities
3. Maintains brand consistency
4. Uses appropriate tone and messaging
"""