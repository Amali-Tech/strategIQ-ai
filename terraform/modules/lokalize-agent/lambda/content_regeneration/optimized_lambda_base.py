# optimized_lambda_base.py - Common optimizations for all Lambda functions
import json
import boto3
import os
import logging
from functools import lru_cache
from typing import Dict, Any

# Configure logging efficiently
logging.basicConfig(level=logging.WARNING)  # Reduce log verbosity
logger = logging.getLogger(__name__)

# Initialize clients outside handler (connection reuse)
BEDROCK_RUNTIME = boto3.client('bedrock-runtime')
MODEL_ID = os.environ.get('MODEL_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')


# Cache for repeated operations
@lru_cache(maxsize=128)
def get_cached_prompt_template(analysis_type: str) -> str:
    """Cache prompt templates to avoid recreation"""
    templates = {
        'cultural_analysis': """Analyze this ad for {target_locale}. Score 1-10 for cultural appropriateness.

Content: {ad_content}

Respond with JSON only:
{{"cultural_score": <number>, "analysis_summary": "<brief summary>", "needs_regeneration": <boolean>}}""",

        'content_regeneration': """Adapt this content for {target_locale}:

Original: {original_content}

Respond with JSON only:
{{"regenerated_content": "<adapted content>", "brand_consistency_score": <number>}}""",

        'translation': """Translate to {target_language}:

Content: {content}

Respond with JSON only:
{{"translated_content": "<translation>", "quality_score": <number>}}"""
    }
    return templates.get(analysis_type, templates['cultural_analysis'])


def invoke_model_optimized(prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
    """Optimized model invocation with reduced token limits"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,  # Reduced from 2000-3000
        "temperature": 0.1,  # Lower temperature for faster, more deterministic responses
        "messages": [{"role": "user", "content": prompt}]
    })

    try:
        response = BEDROCK_RUNTIME.invoke_model(
            modelId=MODEL_ID,
            body=body,
            contentType='application/json'
        )

        result = json.loads(response['body'].read())

        if 'content' in result and len(result['content']) > 0:
            return json.loads(result['content'][0].get('text', '{}'))
        else:
            raise Exception("No content in response")

    except Exception as e:
        logger.error(f"Model invocation error: {e}")
        raise


def create_bedrock_response(event: Dict, result: Dict, status_code: int = 200) -> Dict:
    """Optimized response creation"""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get('actionGroup', 'Unknown'),
            "apiPath": event.get('apiPath', '/'),
            "httpMethod": event.get('httpMethod', 'POST'),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(result)
                }
            }
        }
    }
