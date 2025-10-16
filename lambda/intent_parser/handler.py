import json
import os
import re
import boto3
from botocore.exceptions import ClientError

# Initialize Bedrock Agent Runtime client
bedrock_client = boto3.client('bedrock-agent-runtime')

def lambda_handler(event, context):
    """
    Lambda handler for intent parsing and routing to Bedrock supervisor agent.
    Receives API Gateway requests, parses intent, and invokes appropriate agent workflows.
    """
    try:
        # Log incoming event for debugging
        print(f"Received event: {json.dumps(event)}")
        
        # Parse route and determine intent
        route_key = event.get('routeKey', '')
        http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
        path = event.get('requestContext', {}).get('http', {}).get('path', '')
        
        # Route-based intent parsing
        intent_type = parse_intent_from_route(route_key, http_method, path)
        if not intent_type:
            return create_response(404, {'error': 'Route not found or unsupported'})
        
        # Parse and validate request body
        body = event.get('body', '')
        if not body:
            return create_response(400, {'error': 'Request body is required'})
        
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            return create_response(400, {'error': f'Invalid JSON: {str(e)}'})
        
        # Validate based on intent type
        validation_error = validate_request(intent_type, request_data)
        if validation_error:
            return create_response(400, validation_error)
        
        # Retrieve environment variables
        agent_id = os.environ.get('SUPERVISOR_AGENT_ID')
        agent_alias_id = os.environ.get('SUPERVISOR_AGENT_ALIAS_ID', 'TSTALIASID')
        
        if not agent_id:
            print("ERROR: Missing SUPERVISOR_AGENT_ID environment variable")
            return create_response(500, {'error': 'Server configuration error: missing agent credentials'})
        
        # Validate format
        if not re.match(r'^[A-Za-z0-9-]+$', agent_id) or not re.match(r'^[A-Za-z0-9-]+$', agent_alias_id):
            print("ERROR: Invalid environment variable format")
            return create_response(500, {'error': 'Server configuration error: invalid agent credentials format'})
        
        # Build structured intent for Bedrock agent
        intent = build_intent(intent_type, request_data)
        print(f"Built intent: {json.dumps(intent)}")
        
        # Use Lambda aws_request_id as session ID
        session_id = context.aws_request_id
        
        # Invoke Bedrock supervisor agent
        agent_response = invoke_bedrock_agent(
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
            intent=intent,
            session_id=session_id
        )
        
        return create_response(200, agent_response)
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        print(f"AWS ClientError: {error_code} - {error_message}")
        return create_response(500, {'error': f'Bedrock invocation failed: {error_message}'})
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return create_response(500, {'error': f'Internal server error: {str(e)}'})

def parse_intent_from_route(route_key, http_method, path):
    """
    Parse intent type from API Gateway route information.
    
    Args:
        route_key: API Gateway route key
        http_method: HTTP method
        path: Request path
    
    Returns:
        String indicating intent type or None if unsupported
    """
    # Campaign creation and management
    if route_key == 'POST /campaigns' or (http_method == 'POST' and '/campaigns' in path):
        return 'create_campaign'
    
    # Cultural analysis
    if route_key == 'POST /cultural-analysis' or (http_method == 'POST' and '/cultural-analysis' in path):
        return 'cultural_analysis'
    
    # Market analysis
    if route_key == 'POST /market-analysis' or (http_method == 'POST' and '/market-analysis' in path):
        return 'market_analysis'
    
    # Sentiment analysis
    if route_key == 'POST /sentiment-analysis' or (http_method == 'POST' and '/sentiment-analysis' in path):
        return 'sentiment_analysis'
    
    # Image analysis
    if route_key == 'POST /image-analysis' or (http_method == 'POST' and '/image-analysis' in path):
        return 'image_analysis'
    
    # Translation services
    if route_key == 'POST /translate' or (http_method == 'POST' and '/translate' in path):
        return 'translate_content'
    
    # Comprehensive campaign (uses all agents)
    if route_key == 'POST /comprehensive-campaign' or (http_method == 'POST' and '/comprehensive-campaign' in path):
        return 'comprehensive_campaign'
    
    return None

def validate_request(intent_type, request_data):
    """
    Validate request data based on intent type.
    
    Args:
        intent_type: Type of intent being processed
        request_data: Parsed request body
    
    Returns:
        Dictionary with error message if validation fails, None if valid
    """
    if intent_type == 'create_campaign':
        if not request_data.get('product') or not isinstance(request_data['product'], dict):
            return {'error': 'Product field is required and must be an object'}
        if 'name' not in request_data['product']:
            return {'error': 'Product name is required'}
    
    elif intent_type == 'cultural_analysis':
        if not request_data.get('content'):
            return {'error': 'Content field is required for cultural analysis'}
        if not request_data.get('target_culture'):
            return {'error': 'Target culture is required for cultural analysis'}
    
    elif intent_type in ['market_analysis', 'sentiment_analysis']:
        if not request_data.get('market_parameters'):
            return {'error': 'Market parameters are required'}
    
    elif intent_type == 'image_analysis':
        if not request_data.get('image_url') and not request_data.get('image_base64'):
            return {'error': 'Either image_url or image_base64 is required'}
    
    elif intent_type == 'translate_content':
        if not request_data.get('content'):
            return {'error': 'Content field is required for translation'}
        if not request_data.get('target_language'):
            return {'error': 'Target language is required for translation'}
    
    elif intent_type == 'comprehensive_campaign':
        if not request_data.get('campaign_brief'):
            return {'error': 'Campaign brief is required for comprehensive campaign creation'}
    
    return None

def build_intent(intent_type, request_data):
    """
    Build structured intent for the Bedrock supervisor agent based on intent type.
    
    Args:
        intent_type: Type of intent being processed
        request_data: Parsed request body
    
    Returns:
        Dictionary containing the structured intent with InvokeAgent instructions
    """
    base_intent = {
        'intent_type': intent_type,
        'timestamp': context.aws_request_id if 'context' in globals() else 'unknown',
        'output_format': 'structured_json'
    }
    
    if intent_type == 'create_campaign':
        return {
            **base_intent,
            'task': 'Create a marketing campaign using the campaign generation agent',
            'instructions': 'InvokeAgent: campaign-generation - Use your image-analysis and data-enrichment tools to gather insights, then generate a comprehensive campaign based on the tool results.',
            'context': {
                'product': request_data.get('product'),
                'target_markets': request_data.get('target_markets', ['Global']),
                'campaign_objectives': request_data.get('campaign_objectives', ['awareness']),
                'budget_range': request_data.get('budget_range', 'medium'),
                'timeline': request_data.get('timeline')
            }
        }
    
    elif intent_type == 'cultural_analysis':
        return {
            **base_intent,
            'task': 'Validate cultural appropriateness of campaign content',
            'instructions': 'InvokeAgent: lokalize - Use your cultural-adaptation tool to validate the content against target market cultural norms, then provide a clear assessment of appropriateness.',
            'context': {
                'content': request_data.get('content'),
                'target_culture': request_data.get('target_culture'),
                'content_type': request_data.get('content_type', 'general'),
                'adaptation_level': request_data.get('adaptation_level', 'moderate')
            }
        }
    
    elif intent_type == 'market_analysis':
        return {
            **base_intent,
            'task': 'Conduct comprehensive market analysis',
            'instructions': 'InvokeAgent: voice-of-the-market - Analyze market trends, competitive landscape, and provide strategic insights for the specified market parameters.',
            'context': {
                'market_parameters': request_data.get('market_parameters'),
                'analysis_focus': request_data.get('analysis_focus', ['market_size', 'competitive_analysis']),
                'time_horizon': request_data.get('time_horizon', '1_year')
            }
        }
    
    elif intent_type == 'sentiment_analysis':
        return {
            **base_intent,
            'task': 'Perform sentiment analysis and generate action items',
            'instructions': 'InvokeAgent: voice-of-the-market - Use your sentiment-analysis tool to gather sentiment data, then use your market-analysis tool to generate specific action items based on the sentiment findings.',
            'context': {
                'analysis_parameters': request_data.get('analysis_parameters'),
                'brand_keywords': request_data.get('brand_keywords', []),
                'time_range': request_data.get('time_range', '30d'),
                'channels': request_data.get('channels', ['social_media', 'news_media'])
            }
        }
    
    elif intent_type == 'image_analysis':
        return {
            **base_intent,
            'task': 'Analyze marketing image for effectiveness and cultural sensitivity',
            'instructions': 'InvokeAgent: campaign-generation - Analyze the provided image for visual impact, brand consistency, and cultural appropriateness.',
            'context': {
                'image_url': request_data.get('image_url'),
                'image_base64': request_data.get('image_base64'),
                'analysis_type': request_data.get('analysis_type', 'full'),
                'target_market': request_data.get('target_market', 'global')
            }
        }
    
    elif intent_type == 'translate_content':
        return {
            **base_intent,
            'task': 'Translate marketing content while preserving brand voice',
            'instructions': 'InvokeAgent: lokalize - Translate the provided content to the target language while maintaining brand voice and cultural appropriateness.',
            'context': {
                'content': request_data.get('content'),
                'source_language': request_data.get('source_language', 'en'),
                'target_language': request_data.get('target_language'),
                'content_type': request_data.get('content_type', 'general'),
                'brand_voice': request_data.get('brand_voice', {})
            }
        }
    
    elif intent_type == 'comprehensive_campaign':
        return {
            **base_intent,
            'task': 'Orchestrate comprehensive campaign development using all specialist agents',
            'instructions': 'InvokeAgent: voice-of-the-market - Analyze market conditions and sentiment. InvokeAgent: campaign-generation - Create campaign concepts and analyze visuals. InvokeAgent: lokalize - Adapt all content for target markets. Synthesize all insights into a comprehensive campaign strategy.',
            'context': {
                'campaign_brief': request_data.get('campaign_brief'),
                'target_markets': request_data.get('target_markets', []),
                'budget_range': request_data.get('budget_range', 'medium'),
                'timeline': request_data.get('timeline'),
                'brand_guidelines': request_data.get('brand_guidelines', {}),
                'success_metrics': request_data.get('success_metrics', [])
            }
        }
    
    # Remove None values to keep intent clean
    if 'context' in base_intent:
        base_intent['context'] = {k: v for k, v in base_intent['context'].items() if v is not None}
    
    return base_intent

def invoke_bedrock_agent(agent_id, agent_alias_id, intent, session_id):
    """
    Invoke Bedrock agent with the structured intent and process the response stream.
    """
    input_text = json.dumps(intent)
    print(f"Invoking Bedrock agent {agent_id} with alias {agent_alias_id}, session: {session_id}")
    
    response = bedrock_client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=input_text,
        enableTrace=True,
        endSession=False
    )
    
    return process_response_stream(response.get('completion'))

def process_response_stream(stream):
    """
    Process the Bedrock agent response stream and aggregate chunks.
    """
    if not stream:
        raise Exception("Empty response stream from Bedrock agent")
    
    aggregated_content = []
    trace_events = []
    
    try:
        for event in stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    content = chunk['bytes'].decode('utf-8')
                    aggregated_content.append(content)
                    print(f"Received chunk: {content[:100]}...")
            
            elif 'trace' in event:
                trace = event['trace']
                trace_events.append(trace)
                print(f"TRACE: {trace.get('traceId', 'unknown')}")
            
            elif 'internalServerException' in event:
                error = event['internalServerException']
                error_message = error.get('message', 'Internal server error')
                raise Exception(f"Bedrock agent error: {error_message}")
            
            elif 'validationException' in event:
                error = event['validationException']
                error_message = error.get('message', 'Validation error')
                raise Exception(f"Bedrock agent validation error: {error_message}")
            
            elif 'throttlingException' in event:
                error = event['throttlingException']
                error_message = error.get('message', 'Throttling error')
                raise Exception(f"Bedrock agent throttling error: {error_message}")
    
    except Exception as e:
        print(f"Error processing stream: {str(e)}")
        raise
    
    full_content = ''.join(aggregated_content)
    
    if not full_content:
        if trace_events:
            print("Warning: No content chunks received, only trace events")
            return {'status': 'completed', 'trace': trace_events, 'content': None}
        else:
            raise Exception("No content received from Bedrock agent")
    
    try:
        parsed_response = json.loads(full_content)
        return parsed_response
    except json.JSONDecodeError:
        print("Warning: Response is not valid JSON, returning as text")
        return {'content': full_content}

def create_response(status_code, body):
    """
    Create a standardized API Gateway response.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body)
    }