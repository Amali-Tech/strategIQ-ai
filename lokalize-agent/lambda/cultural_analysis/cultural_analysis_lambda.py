# lambda/cultural_analysis/cultural_analysis_lambda.py
import json
import boto3
import os
import logging
from optimized_lambda_base import invoke_model_optimized, create_bedrock_response

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Cultural analysis Lambda for Bedrock Agents
    Must return response in Bedrock Agent format
    """

    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Extract parameters from Bedrock Agent event
        # Bedrock sends parameters in a specific format
        if 'requestBody' in event and 'content' in event['requestBody']:
            # Parse the request body
            content = event['requestBody']['content']
            if isinstance(content, dict):
                # Direct parameter access
                ad_content = content.get('ad_content', '')
                target_locale = content.get('target_locale', '')
                content_type = content.get('content_type', 'text')
                brand_guidelines = content.get('brand_guidelines', '')
            else:
                # Parse JSON string
                params = json.loads(content) if isinstance(content, str) else content
                ad_content = params.get('ad_content', '')
                target_locale = params.get('target_locale', '')
                content_type = params.get('content_type', 'text')
                brand_guidelines = params.get('brand_guidelines', '')
        else:
            # Fallback: try to extract from different event structures
            body = event.get('body', '{}')
            if isinstance(body, str):
                params = json.loads(body)
            else:
                params = body

            ad_content = params.get('ad_content', '')
            target_locale = params.get('target_locale', '')
            content_type = params.get('content_type', 'text')
            brand_guidelines = params.get('brand_guidelines', '')

        logger.info(f"Parameters - Content: {ad_content[:100]}..., Locale: {target_locale}")

        # Perform analysis
        analysis_result = analyze_content_with_nova(
            ad_content, target_locale, content_type, brand_guidelines
        )

        # Return in Bedrock Agent format
        logger.info("Analysis completed successfully")
        return create_bedrock_response(event, analysis_result)

    except Exception as e:
        logger.error(f"Error in cultural analysis: {str(e)}")

        # Return error in Bedrock Agent format
        error_result = {
            "error": str(e),
            "cultural_score": 5.0,
            "analysis_summary": f"Analysis failed due to technical error: {str(e)}",
            "cultural_issues": [
                {"issue": "Technical error", "severity": "high", "explanation": str(e)}],
            "recommendations": [{"recommendation": "Manual review required", "priority": "high",
                                 "rationale": "Automated analysis failed"}],
            "needs_regeneration": True
        }

        return create_bedrock_response(event, error_result, 500)


def analyze_content_with_nova(
        ad_content: str,
        target_locale: str,
        content_type: str,
        brand_guidelines: str
) -> dict:
    """Perform cultural analysis using Amazon Nova Pro with optimized prompts"""

    if not ad_content or not target_locale:
        return {
            "cultural_score": 5.0,
            "analysis_summary": "Insufficient information provided for analysis",
            "cultural_issues": [{"issue": "Missing required parameters", "severity": "high",
                                 "explanation": "Ad content or target locale not provided"}],
            "recommendations": [{"recommendation": "Provide complete ad content and target locale", "priority": "high",
                                 "rationale": "Required for analysis"}],
            "needs_regeneration": True
        }

    analysis_prompt = f"""Analyze this {content_type} for cultural appropriateness in {target_locale}. Score 1-10.

CONTENT: {ad_content}
TARGET: {target_locale}
BRAND GUIDELINES: {brand_guidelines if brand_guidelines else "None"}

Consider cultural values, communication styles, taboos, and local preferences.

Respond with ONLY valid JSON:
{{
    "cultural_score": <1-10 number>,
    "analysis_summary": "<brief 2-3 sentence summary>",
    "cultural_issues": [
        {{"issue": "<issue>", "severity": "low|medium|high", "explanation": "<explanation>"}}
    ],
    "recommendations": [
        {{"recommendation": "<action>", "priority": "low|medium|high", "rationale": "<reason>"}}
    ],
    "needs_regeneration": <true if score < 7>
}}"""

    try:
        result = invoke_model_optimized(analysis_prompt, max_tokens=1200)
        
        # Validate required fields
        required_fields = ['cultural_score', 'analysis_summary', 'needs_regeneration']
        for field in required_fields:
            if field not in result:
                result[field] = get_default_value(field)

        # Ensure arrays exist
        if 'cultural_issues' not in result:
            result['cultural_issues'] = []
        if 'recommendations' not in result:
            result['recommendations'] = []

        return result

    except Exception as e:
        logger.error(f"Error in cultural analysis: {e}")
        return create_fallback_response(target_locale, str(e))


def get_default_value(field: str):
    """Get default values for required fields"""
    defaults = {
        'cultural_score': 6.0,
        'analysis_summary': 'Analysis completed with limited information',
        'needs_regeneration': True
    }
    return defaults.get(field, None)


def create_fallback_response(target_locale: str, error_msg: str) -> dict:
    """Create a fallback response when analysis fails"""
    return {
        'cultural_score': 5.0,
        'analysis_summary': f'Cultural analysis for {target_locale} encountered technical difficulties. Manual review recommended.',
        'cultural_issues': [
            {
                'issue': 'Technical analysis limitation',
                'severity': 'medium',
                'explanation': f'Automated analysis failed: {error_msg}'
            }
        ],
        'recommendations': [
            {
                'recommendation': 'Conduct manual cultural review',
                'priority': 'high',
                'rationale': 'Automated analysis was unable to complete successfully'
            }
        ],
        'needs_regeneration': True,
        'error_details': error_msg
    }
