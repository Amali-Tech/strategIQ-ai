# lambda/translation/translation_lambda.py
import json
import boto3
import os
import logging

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
                content_to_translate = content.get('content', '')
                target_language = content.get('target_language', '')
                source_language = content.get('source_language', 'en')
                content_type = content.get('content_type', 'marketing_copy')
            else:
                params = json.loads(content) if isinstance(content, str) else content
                content_to_translate = params.get('content', '')
                target_language = params.get('target_language', '')
                source_language = params.get('source_language', 'en')
                content_type = params.get('content_type', 'marketing_copy')
        else:
            body = event.get('body', '{}')
            if isinstance(body, str):
                params = json.loads(body)
            else:
                params = body

            content_to_translate = params.get('content', '')
            target_language = params.get('target_language', '')
            source_language = params.get('source_language', 'en')
            content_type = params.get('content_type', 'marketing_copy')

        logger.info(f"Translating from {source_language} to {target_language}")

        # Perform translation
        translation_result = translate_with_claude(
            content_to_translate, target_language, source_language, content_type
        )

        # Return in Bedrock Agent format
        bedrock_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'Translation'),
                "apiPath": event.get('apiPath', '/translate'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(translation_result)
                    }
                }
            }
        }

        logger.info("Translation completed successfully")
        return bedrock_response

    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")

        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'Translation'),
                "apiPath": event.get('apiPath', '/translate'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({
                            "error": str(e),
                            "translated_content": "Translation failed due to technical error",
                            "translation_notes": [],
                            "cultural_adaptations": [],
                            "quality_score": 0.0
                        })
                    }
                }
            }
        }

        return error_response


def translate_with_claude(
        content: str,
        target_language: str,
        source_language: str,
        content_type: str
) -> dict:
    """Translate content using Claude 3.5 Sonnet"""

    if not content or not target_language:
        return {
            "translated_content": "Unable to translate: missing content or target language",
            "translation_notes": [],
            "cultural_adaptations": ["Provide content and target language"],
            "quality_score": 0.0
        }

    bedrock_runtime = boto3.client('bedrock-runtime')
    model_id = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'

    translation_prompt = f"""You are an expert translator specializing in marketing content. Translate this {content_type} from {source_language} to {target_language}.

CONTENT TO TRANSLATE:
{content}

SOURCE LANGUAGE: {source_language}
TARGET LANGUAGE: {target_language}
CONTENT TYPE: {content_type}

Provide a culturally-appropriate translation that:
1. Preserves marketing intent and impact
2. Adapts to cultural communication styles
3. Uses appropriate formality level
4. Maintains brand voice while localizing

Respond with ONLY valid JSON in this exact format:
{{
    "translated_content": "<the translated content>",
    "translation_notes": [
        {{"original_phrase": "<phrase>", "translated_phrase": "<translation>", "note": "<explanation>"}}
    ],
    "cultural_adaptations": ["<adaptation 1>", "<adaptation 2>"],
    "quality_score": <number between 1-10>
}}"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": translation_prompt
            }
        ]
    })

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json'
        )

        result = json.loads(response['body'].read())

        if 'content' in result and len(result['content']) > 0:
            content_text = result['content'][0].get('text', '{}')
        else:
            raise Exception("No content in Claude response")

        try:
            parsed_result = json.loads(content_text)

            # Validate required fields
            if 'translated_content' not in parsed_result:
                parsed_result['translated_content'] = f"[Translated to {target_language}] {content}"
            if 'quality_score' not in parsed_result:
                parsed_result['quality_score'] = 7.0

            # Ensure arrays exist
            if 'translation_notes' not in parsed_result:
                parsed_result['translation_notes'] = []
            if 'cultural_adaptations' not in parsed_result:
                parsed_result['cultural_adaptations'] = []

            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return create_translation_fallback(content, target_language, str(e))

    except Exception as e:
        logger.error(f"Error invoking Claude: {e}")
        return create_translation_fallback(content, target_language, str(e))


def create_translation_fallback(content: str, target_language: str, error_msg: str) -> dict:
    """Create fallback response for translation"""
    return {
        'translated_content': f"[Translation to {target_language} attempted] {content}",
        'translation_notes': [
            {
                'original_phrase': 'entire content',
                'translated_phrase': 'technical limitation',
                'note': f'Automated translation failed: {error_msg}'
            }
        ],
        'cultural_adaptations': [
            'Manual translation recommended',
            'Technical limitation in automated process'
        ],
        'quality_score': 4.0,
        'error_details': error_msg
    }
