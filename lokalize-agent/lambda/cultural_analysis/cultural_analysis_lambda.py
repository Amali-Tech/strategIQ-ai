# lambda/cultural_analysis/cultural_analysis_lambda.py
import json
import boto3
import os
import logging

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
        bedrock_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'CulturalAnalysis'),
                "apiPath": event.get('apiPath', '/analyze'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(analysis_result)
                    }
                }
            }
        }

        logger.info("Analysis completed successfully")
        return bedrock_response

    except Exception as e:
        logger.error(f"Error in cultural analysis: {str(e)}")

        # Return error in Bedrock Agent format
        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'CulturalAnalysis'),
                "apiPath": event.get('apiPath', '/analyze'),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({
                            "error": str(e),
                            "cultural_score": 5.0,
                            "analysis_summary": f"Analysis failed due to technical error: {str(e)}",
                            "cultural_issues": [
                                {"issue": "Technical error", "severity": "high", "explanation": str(e)}],
                            "recommendations": [{"recommendation": "Manual review required", "priority": "high",
                                                 "rationale": "Automated analysis failed"}],
                            "needs_regeneration": True
                        })
                    }
                }
            }
        }

        return error_response


def analyze_content_with_nova(
        ad_content: str,
        target_locale: str,
        content_type: str,
        brand_guidelines: str
) -> dict:
    """Perform cultural analysis using Amazon Nova Pro"""

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

    bedrock_runtime = boto3.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'

    analysis_prompt = f"""You are an expert cultural marketing analyst. Analyze this {content_type} advertisement for {target_locale}.

ADVERTISEMENT CONTENT:
{ad_content}

TARGET LOCALE: {target_locale}
BRAND GUIDELINES: {brand_guidelines if brand_guidelines else "None provided"}

Provide a comprehensive cultural analysis. Consider:
- Cultural values and beliefs in {target_locale}
- Communication styles and preferences  
- Visual and aesthetic preferences
- Cultural taboos and sensitivities
- Local business practices
- Seasonal and religious considerations

Respond with ONLY valid JSON in this exact format:
{{
    "cultural_score": <number between 1-10>,
    "analysis_summary": "<detailed summary in 2-3 sentences>",
    "cultural_issues": [
        {{"issue": "<specific issue>", "severity": "low|medium|high", "explanation": "<why this is an issue>"}}
    ],
    "recommendations": [
        {{"recommendation": "<specific actionable recommendation>", "priority": "low|medium|high", "rationale": "<why this recommendation>"}}
    ],
    "needs_regeneration": <true if score < 7, false otherwise>
}}"""

    # Amazon Nova Pro message format
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": analysis_prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 2000,
            "temperature": 0.3
        }
    })

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json'
        )

        result = json.loads(response['body'].read())

        # Extract Nova's response
        if 'output' in result and 'message' in result['output']:
            content = result['output']['message'].get('content', [])
            if content and len(content) > 0:
                content_text = content[0].get('text', '{}')
            else:
                raise Exception("No content in Nova response")
        else:
            raise Exception("No output message in Nova response")

        # Parse JSON response
        try:
            parsed_result = json.loads(content_text)

            # Validate required fields
            required_fields = ['cultural_score', 'analysis_summary', 'needs_regeneration']
            for field in required_fields:
                if field not in parsed_result:
                    parsed_result[field] = get_default_value(field)

            # Ensure arrays exist
            if 'cultural_issues' not in parsed_result:
                parsed_result['cultural_issues'] = []
            if 'recommendations' not in parsed_result:
                parsed_result['recommendations'] = []

            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, Content: {content_text}")
            return create_fallback_response(target_locale, f"JSON parsing failed: {str(e)}")

    except Exception as e:
        logger.error(f"Error invoking Nova: {e}")
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
