# lambda/translation/translation_lambda.py
import json
import boto3
import os
import logging
from optimized_lambda_base import invoke_model_optimized, create_bedrock_response, get_cached_prompt_template

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Translation Lambda for Bedrock Agents"""

    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Extract parameters from Bedrock Agent event
        if 'requestBody' in event and 'content' in event['requestBody']:
            content = event['requestBody']['content']
            if isinstance(content, dict):
                source_content = content.get('content', '')
                target_language = content.get('target_language', '')
                content_type = content.get('content_type', 'text')
                preserve_formatting = content.get('preserve_formatting', True)
                brand_voice = content.get('brand_voice', '')
            else:
                params = json.loads(content) if isinstance(content, str) else content
                source_content = params.get('content', '')
                target_language = params.get('target_language', '')
                content_type = params.get('content_type', 'text')
                preserve_formatting = params.get('preserve_formatting', True)
                brand_voice = params.get('brand_voice', '')
        else:
            body = event.get('body', '{}')
            if isinstance(body, str):
                params = json.loads(body)
            else:
                params = body

            source_content = params.get('content', '')
            target_language = params.get('target_language', '')
            content_type = params.get('content_type', 'text')
            preserve_formatting = params.get('preserve_formatting', True)
            brand_voice = params.get('brand_voice', '')

        logger.info(f"Translating {content_type} to {target_language}")

        # Perform translation
        translation_result = translate_content_with_nova(
            source_content, target_language, content_type, preserve_formatting, brand_voice
        )

        # Return in Bedrock Agent format
        return create_bedrock_response(event, translation_result)

    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")

        error_response = {
            "error": str(e),
            "translated_content": "Translation failed due to technical error",
            "quality_score": 0.0,
            "translation_notes": ["Technical error occurred during translation"],
            "confidence_level": "low"
        }

        return create_bedrock_response(event, error_response, 500)


def translate_content_with_nova(
        source_content: str,
        target_language: str,
        content_type: str,
        preserve_formatting: bool,
        brand_voice: str
) -> dict:
    """Translate content using Amazon Nova Pro with optimized prompts"""

    if not source_content or not target_language:
        return {
            "translated_content": "Unable to translate: missing source content or target language",
            "quality_score": 0.0,
            "translation_notes": ["Provide complete source content and target language"],
            "confidence_level": "low"
        }

    # Build optimized translation prompt
    formatting_instruction = "Preserve original formatting, structure, and style." if preserve_formatting else "Adapt formatting for target language conventions."
    brand_instruction = f"Maintain brand voice: {brand_voice}" if brand_voice else "Maintain original tone and style."

    translation_prompt = f"""Translate this {content_type} to {target_language}. {formatting_instruction} {brand_instruction}

SOURCE CONTENT:
{source_content}

TARGET LANGUAGE: {target_language}

Requirements:
- Accurate, culturally appropriate translation
- Maintain marketing effectiveness
- Preserve key messaging and calls-to-action
- Use native-speaker level fluency

Respond with ONLY valid JSON:
{{
    "translated_content": "<complete translation>",
    "quality_score": <1-10 rating>,
    "translation_notes": ["<any important notes>"],
    "confidence_level": "low|medium|high"
}}"""

    try:
        result = invoke_model_optimized(translation_prompt, max_tokens=1500)
        
        # Validate required fields
        required_fields = ['translated_content', 'quality_score', 'confidence_level']
        for field in required_fields:
            if field not in result:
                result[field] = get_default_translation_value(field)

        # Ensure arrays exist
        if 'translation_notes' not in result:
            result['translation_notes'] = []

        return result

    except Exception as e:
        logger.error(f"Error in translation: {e}")
        return create_fallback_translation_response(target_language, str(e))


def get_default_translation_value(field: str):
    """Get default values for required translation fields"""
    defaults = {
        'translated_content': 'Translation unavailable',
        'quality_score': 5.0,
        'confidence_level': 'medium'
    }
    return defaults.get(field, None)


def create_fallback_translation_response(target_language: str, error_msg: str) -> dict:
    """Create a fallback response when translation fails"""
    return {
        'translated_content': f'Translation to {target_language} encountered technical difficulties. Manual translation recommended.',
        'quality_score': 3.0,
        'translation_notes': [
            f'Automated translation failed: {error_msg}',
            'Manual review and translation recommended'
        ],
        'confidence_level': 'low',
        'error_details': error_msg
    }