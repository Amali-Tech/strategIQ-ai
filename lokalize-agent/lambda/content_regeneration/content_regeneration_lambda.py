# lambda/content_regeneration/content_regeneration_lambda.py
import json
import boto3
import os
import logging
from optimized_lambda_base import invoke_model_optimized, create_bedrock_response

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
        logger.info("Content regeneration completed successfully")
        return create_bedrock_response(event, regeneration_result)

    except Exception as e:
        logger.error(f"Error in content regeneration: {str(e)}")

        error_result = {
            "error": str(e),
            "regenerated_content": "Content regeneration failed due to technical error",
            "adaptations_made": [],
            "cultural_improvements": [],
            "brand_consistency_score": 0.0
        }

        return create_bedrock_response(event, error_result, 500)


def regenerate_content_with_nova(
        original_content: str,
        target_locale: str,
        adaptation_level: str,
        brand_voice: str,
        content_type: str
) -> dict:
    """Regenerate content using Amazon Nova Pro with optimized prompts"""

    if not original_content or not target_locale:
        return {
            "regenerated_content": "Unable to regenerate: missing original content or target locale",
            "adaptations_made": [],
            "cultural_improvements": ["Provide complete original content and target locale"],
            "brand_consistency_score": 0.0
        }

    regeneration_prompt = f"""Regenerate this {content_type} for {target_locale} with {adaptation_level} cultural adaptation.

ORIGINAL: {original_content}
TARGET: {target_locale}
BRAND VOICE: {brand_voice if brand_voice else "Maintain original"}

Requirements:
- Culturally appropriate for {target_locale}
- Maintain brand consistency
- {adaptation_level} level of cultural adaptation
- Preserve marketing effectiveness

Respond with ONLY valid JSON:
{{
    "regenerated_content": "<complete regenerated content>",
    "adaptations_made": ["<list of changes made>"],
    "cultural_improvements": ["<cultural enhancements>"],
    "brand_consistency_score": <1-10 rating>
}}"""

    try:
        result = invoke_model_optimized(regeneration_prompt, max_tokens=1500)
        
        # Validate required fields
        required_fields = ['regenerated_content', 'brand_consistency_score']
        for field in required_fields:
            if field not in result:
                result[field] = get_default_regeneration_value(field)

        # Ensure arrays exist
        if 'adaptations_made' not in result:
            result['adaptations_made'] = []
        if 'cultural_improvements' not in result:
            result['cultural_improvements'] = []

        return result

    except Exception as e:
        logger.error(f"Error in content regeneration: {e}")
        return create_fallback_regeneration_response(target_locale, str(e))


def get_default_regeneration_value(field: str):
    """Get default values for required regeneration fields"""
    defaults = {
        'regenerated_content': 'Content regeneration unavailable',
        'brand_consistency_score': 6.0
    }
    return defaults.get(field, None)


def create_fallback_regeneration_response(target_locale: str, error_msg: str) -> dict:
    """Create a fallback response when regeneration fails"""
    return {
        'regenerated_content': f'Content regeneration for {target_locale} encountered technical difficulties. Manual adaptation recommended.',
        'adaptations_made': ['Technical error occurred'],
        'cultural_improvements': [f'Automated regeneration failed: {error_msg}'],
        'brand_consistency_score': 5.0,
        'error_details': error_msg
    }