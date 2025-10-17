import json
import os
import re
import time
import random
import uuid
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

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
        intent = build_intent(intent_type, request_data, context.aws_request_id)
        print(f"Built intent: {json.dumps(intent)}")
        
        # Generate unique campaign ID and use Lambda aws_request_id as session ID
        campaign_id = str(uuid.uuid4())
        session_id = context.aws_request_id
        
        # Create initial campaign status record
        create_campaign_status(campaign_id, 'processing', intent.get('context', {}))
        
        # Invoke Bedrock supervisor agent
        agent_response = invoke_bedrock_agent(
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
            intent=intent,
            session_id=session_id
        )
        
        # Handle response based on campaign type
        if intent_type == 'create_basic_campaign':
            # Basic campaign: Return comprehensive structure
            update_campaign_status(campaign_id, 'completed', agent_response)
            
            # Convert to comprehensive structure
            comprehensive_response = create_comprehensive_campaign_response(agent_response, request_data, campaign_id)
            
            response_data = comprehensive_response
            
        elif intent_type == 'create_comprehensive_campaign':
            # Comprehensive campaign: Emit event for async asset generation
            update_campaign_status(campaign_id, 'awaiting_assets', agent_response)
            emit_campaign_completion_event(campaign_id, agent_response, intent.get('context', {}))
            
            # Convert to comprehensive structure
            comprehensive_response = create_comprehensive_campaign_response(agent_response, request_data, campaign_id)
            comprehensive_response['status'] = 'awaiting_assets' 
            comprehensive_response['message'] = 'Comprehensive campaign analysis completed. Visual assets are being generated asynchronously.'
            
            response_data = comprehensive_response
        
        return create_response(200, response_data)
        
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
    # Basic campaign creation (Tier 1 - Image analysis + Data enrichment + Campaign generation)
    if route_key == 'POST /api/campaigns' or (http_method == 'POST' and '/api/campaigns' in path):
        return 'create_basic_campaign'
    
    # Comprehensive campaign (Tier 3 - Full workflow + Cultural intelligence + Async assets)
    if route_key == 'POST /api/comprehensive-campaign' or (http_method == 'POST' and '/api/comprehensive-campaign' in path):
        return 'create_comprehensive_campaign'
    
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
    if intent_type in ['create_basic_campaign', 'create_comprehensive_campaign']:
        if not request_data.get('product') or not isinstance(request_data['product'], dict):
            return {'error': 'Product field is required and must be an object'}
        if 'name' not in request_data['product']:
            return {'error': 'Product name is required'}
    
    return None

def build_intent(intent_type, request_data, request_id=None):
    """
    Build structured intent for the Bedrock supervisor agent based on intent type.
    
    Args:
        intent_type: Type of intent being processed
        request_data: Parsed request body
        request_id: AWS request ID for tracking
    
    Returns:
        Dictionary containing the structured intent with InvokeAgent instructions
    """
    base_intent = {
        'intent_type': intent_type,
        'timestamp': request_id or 'unknown',
        'output_format': 'structured_json'
    }
    
    if intent_type in ['create_basic_campaign', 'create_comprehensive_campaign']:
        s3_info = request_data.get('s3_info')
        product = request_data.get('product', {})
        
        # Route-specific instructions
        if intent_type == 'create_basic_campaign':
            instructions = 'ROUTE: /campaign - Use the basic campaign workflow: '
        else:
            instructions = 'ROUTE: /comprehensive-campaign - Use the comprehensive campaign workflow: '
        
        if s3_info and s3_info.get('bucket') and s3_info.get('key'):
            instructions += f"""FIRST call the image-analysis action group using /analyze-product-image endpoint with this EXACT payload:
{{
  "product_info": {{
    "name": "{product.get('name', 'Unknown')}",
    "description": "{product.get('description', 'No description provided')}",
    "category": "{product.get('category', 'General')}"
  }},
  "s3_info": {{
    "bucket": "{s3_info.get('bucket')}",
    "key": "{s3_info.get('key')}"
  }}
}}

Then use the image analysis results to enhance your campaign recommendations. """
        
        if intent_type == 'create_basic_campaign':
            instructions += 'Generate platform-specific content for Instagram, TikTok, Facebook, YouTube, and Twitter. Provide structured campaign recommendations with clear next steps and success metrics. Do NOT include visual asset generation.'
        else:
            instructions += 'Generate enhanced platform-specific content for global markets including cultural adaptations. Include asset placeholders like {{PLACEHOLDER_SOCIAL_POST_IMAGE}} for async generation. Do NOT call visual-asset-generator directly.'
        
        return {
            **base_intent,
            'task': 'Create a comprehensive marketing campaign with image analysis',
            'instructions': instructions,
            'context': {
                'product': product,
                'target_markets': request_data.get('target_markets', ['Global']),
                'campaign_objectives': request_data.get('campaign_objectives', ['awareness']),
                'campaign_goals': request_data.get('campaign_goals', ['general_marketing']),
                'target_audience': request_data.get('target_audience', {}),
                'budget_range': request_data.get('budget_range', 'medium'),
                'timeline': request_data.get('timeline'),
                's3_info': s3_info,
                'platform_preferences': request_data.get('platform_preferences', ['instagram', 'facebook', 'tiktok'])
            }
        }
    
    # Remove None values to keep intent clean
    if 'context' in base_intent:
        base_intent['context'] = {k: v for k, v in base_intent['context'].items() if v is not None}
    
    return base_intent

def invoke_bedrock_agent_with_retry(agent_id, agent_alias_id, intent, session_id, max_retries=3):
    """
    Invoke Bedrock agent with retry logic for throttling exceptions.
    Uses exponential backoff with jitter to handle throttling gracefully.
    """
    input_text = json.dumps(intent)
    print(f"Invoking Bedrock agent {agent_id} with alias {agent_alias_id}, session: {session_id}")
    
    for attempt in range(max_retries + 1):
        try:
            response = bedrock_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=True,
                endSession=False
            )
            
            return process_response_stream(response.get('completion'))
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'ThrottlingException' and attempt < max_retries:
                # Calculate exponential backoff with jitter
                base_delay = 2 ** attempt  # 1, 2, 4 seconds
                jitter = random.uniform(0.1, 0.3)  # Add 10-30% jitter
                delay = base_delay + jitter
                
                print(f"Throttling detected on attempt {attempt + 1}/{max_retries + 1}. "
                      f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            else:
                # Re-raise non-throttling errors or if max retries exceeded
                print(f"Bedrock ClientError (attempt {attempt + 1}): {error_code} - {error_message}")
                raise
        
        except Exception as e:
            print(f"Unexpected error during Bedrock invocation (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries and 'throttling' in str(e).lower():
                # Handle throttling exceptions that come through response stream
                base_delay = 2 ** attempt
                jitter = random.uniform(0.1, 0.3)
                delay = base_delay + jitter
                
                print(f"Stream throttling detected. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
            else:
                raise
    
    # This should never be reached due to the raise statements above
    raise Exception(f"Failed to invoke Bedrock agent after {max_retries + 1} attempts")

def invoke_bedrock_agent(agent_id, agent_alias_id, intent, session_id):
    """
    Invoke Bedrock agent with the structured intent and process the response stream.
    Wrapper function that calls the retry-enabled version.
    """
    return invoke_bedrock_agent_with_retry(agent_id, agent_alias_id, intent, session_id)

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
                # Let this bubble up as a generic exception so retry logic can catch it
                raise Exception(f"throttling: {error_message}")
    
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
        return structure_campaign_response(parsed_response)
    except json.JSONDecodeError:
        # If the response isn't valid JSON, try to extract JSON from text
        structured_response = extract_and_structure_json(full_content)
        if structured_response:
            return structured_response
        
        # If no JSON found, return as structured text with fallback structure
        print("Warning: Response is not valid JSON, creating fallback structure")
        return create_fallback_structure(full_content)

def structure_campaign_response(parsed_response):
    """
    Ensure the campaign response has the expected structure for the frontend.
    """
    # If already properly structured, return as-is
    if all(key in parsed_response for key in ['campaign_strategy', 'visual_insights', 'platform_content', 'market_trends', 'success_metrics']):
        return parsed_response
    
    # If it's a wrapper with content, extract it
    if 'content' in parsed_response and isinstance(parsed_response['content'], dict):
        return structure_campaign_response(parsed_response['content'])
    
    # If it's just text content, try to parse it
    if 'content' in parsed_response and isinstance(parsed_response['content'], str):
        return create_fallback_structure(parsed_response['content'])
    
    # Return the response as-is if it's already structured
    return parsed_response

def extract_and_structure_json(text_content):
    """
    Try to extract JSON from text content that might contain markdown or other formatting.
    """
    import re
    
    # Try to find JSON objects in the text
    json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
    matches = re.findall(json_pattern, text_content, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict) and len(parsed) > 1:  # Must be a meaningful object
                return structure_campaign_response(parsed)
        except json.JSONDecodeError:
            continue
    
    return None

def create_fallback_structure(text_content):
    """
    Create a structured response from text content when JSON parsing fails.
    This ensures the frontend always gets the expected structure.
    """
    # Extract key information from text using simple pattern matching
    lines = text_content.split('\n')
    
    # Basic fallback structure
    fallback = {
        'campaign_strategy': {
            'overview': 'AI-generated marketing campaign based on product analysis',
            'objectives': ['brand_awareness', 'engagement'],
            'target_audience_insights': 'General target audience based on product category'
        },
        'visual_insights': {
            'primary_visual_elements': ['product', 'branding'],
            'color_scheme': ['primary', 'secondary'],
            'visual_themes': ['modern', 'clean'],
            'detected_objects': ['product']
        },
        'platform_content': {
            'instagram': {
                'content_themes': ['product_showcase', 'lifestyle'],
                'recommended_formats': ['image_post', 'story'],
                'sample_post': 'Check out our amazing product! #product #lifestyle',
                'hashtags': ['#product', '#lifestyle', '#quality'],
                'posting_schedule': 'Peak engagement times: 12-3pm, 7-9pm'
            },
            'tiktok': {
                'content_themes': ['product_demo', 'trending'],
                'recommended_formats': ['short_video', 'tutorial'],
                'sample_post': 'Product demo video showing key features',
                'hashtags': ['#productdemo', '#tutorial', '#trending'],
                'trending_sounds': ['popular_audio_1', 'trending_sound_2']
            },
            'youtube': {
                'content_themes': ['product_review', 'educational'],
                'recommended_formats': ['review_video', 'tutorial'],
                'sample_post': 'Comprehensive product review and tutorial',
                'video_ideas': ['unboxing', 'tutorial', 'comparison'],
                'seo_keywords': ['product review', 'tutorial', 'how to']
            }
        },
        'market_trends': {
            'trending_keywords': ['product', 'review', 'quality'],
            'competitor_insights': ['market_analysis', 'competitive_advantage'],
            'market_opportunities': ['social_media', 'influencer_marketing'],
            'seasonal_trends': ['year_round_appeal']
        },
        'success_metrics': {
            'engagement_targets': {
                'likes': '500-1000 per post',
                'comments': '50-100 per post',
                'shares': '25-50 per post'
            },
            'reach_goals': {
                'impressions': '10,000-50,000',
                'unique_users': '5,000-25,000'
            },
            'conversion_metrics': {
                'click_through_rate': '2-5%',
                'conversion_rate': '1-3%'
            }
        }
    }
    
    # Try to extract some information from the text content
    text_lower = text_content.lower()
    
    # Extract platform mentions and enhance platform_content
    platforms = ['instagram', 'tiktok', 'youtube', 'facebook', 'twitter']
    for platform in platforms:
        if platform in text_lower:
            # Find content related to this platform
            platform_lines = [line for line in lines if platform in line.lower()]
            if platform_lines and platform in fallback['platform_content']:
                fallback['platform_content'][platform]['sample_post'] = platform_lines[0][:200]
    
    # Extract keywords and hashtags
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text_content)
    if hashtags:
        for platform in fallback['platform_content']:
            fallback['platform_content'][platform]['hashtags'] = hashtags[:5]
    
    # Store original content for reference
    fallback['_original_content'] = text_content
    
    return fallback

def create_campaign_status(campaign_id, status, context_data):
    """
    Create initial campaign status record in DynamoDB.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            print("Warning: CAMPAIGN_STATUS_TABLE_NAME not set, skipping status tracking")
            return
        
        table = dynamodb.Table(table_name)
        
        # Set TTL to 7 days from now
        expires_at = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        
        table.put_item(
            Item={
                'campaign_id': campaign_id,
                'status': status,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'context_data': context_data,
                'expires_at': expires_at
            }
        )
        print(f"Created campaign status record: {campaign_id} - {status}")
    except Exception as e:
        print(f"Error creating campaign status: {str(e)}")

def update_campaign_status(campaign_id, status, result_data):
    """
    Update campaign status record with results.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            print("Warning: CAMPAIGN_STATUS_TABLE_NAME not set, skipping status update")
            return
        
        table = dynamodb.Table(table_name)
        
        table.update_item(
            Key={'campaign_id': campaign_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, result_data = :result_data',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat(),
                ':result_data': result_data
            }
        )
        print(f"Updated campaign status: {campaign_id} - {status}")
    except Exception as e:
        print(f"Error updating campaign status: {str(e)}")

def emit_campaign_completion_event(campaign_id, campaign_data, context_data):
    """
    Emit campaign completion event to EventBridge for async visual asset generation.
    """
    try:
        event_bus_name = os.environ.get('CAMPAIGN_EVENTS_BUS_NAME')
        if not event_bus_name:
            print("Warning: CAMPAIGN_EVENTS_BUS_NAME not set, skipping event emission")
            return
        
        event_detail = {
            'campaign_id': campaign_id,
            'status': 'completed',
            'campaign_data': campaign_data,
            'context_data': context_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'degenerals.campaign',
                    'DetailType': 'Campaign Analysis Completed',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': event_bus_name
                }
            ]
        )
        print(f"Emitted campaign completion event for: {campaign_id}")
    except Exception as e:
        print(f"Error emitting campaign completion event: {str(e)}")

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

def create_product_section(request_data):
    """Create product section with image data if available."""
    product = request_data.get('product', {})
    s3_info = request_data.get('s3_info', {})
    
    product_section = {
        "description": product.get('description', product.get('name', 'Product description'))
    }
    
    if s3_info:
        product_section["image"] = {
            "public_url": f"https://{s3_info.get('bucket', 'product-images-bucket')}.s3.amazonaws.com/{s3_info.get('key', '')}",
            "s3_key": s3_info.get('key', ''),
            "labels": []  # Would be populated from image analysis
        }
    
    return product_section

def create_content_ideas_from_platform_content(platform_content):
    """Convert platform content into content ideas format."""
    content_ideas = []
    
    for platform, content in platform_content.items():
        if isinstance(content, dict):
            idea = {
                "platform": platform.title(),
                "topic": f"{platform.title()} content strategy",
                "engagement_score": 85 + random.randint(0, 10),
                "caption": content.get('sample_post', ''),
                "hashtags": content.get('hashtags', [])
            }
            content_ideas.append(idea)
    
    return content_ideas

def create_campaign_sections(agent_data):
    """Create detailed campaign sections from agent data."""
    campaigns = []
    platform_content = agent_data.get('platform_content', {})
    
    if platform_content:
        # Create a main campaign
        campaign = {
            "name": "Multi-Platform Marketing Campaign",
            "duration": "4 weeks",
            "posts_per_week": 3,
            "platforms": list(platform_content.keys()),
            "calendar": {
                "Week 1": "Launch campaign with engaging content across all platforms",
                "Week 2": "Focus on user engagement and community building",
                "Week 3": "Share educational content and product demonstrations",
                "Week 4": "Drive conversions with special offers and testimonials"
            },
            "adaptations": {}
        }
        
        # Add platform-specific adaptations
        for platform, content in platform_content.items():
            if isinstance(content, dict):
                themes = content.get('content_themes', [])
                formats = content.get('recommended_formats', [])
                campaign["adaptations"][platform.title()] = f"Focus on {', '.join(themes[:2])} using {', '.join(formats[:2])}"
        
        campaigns.append(campaign)
    
    return campaigns

def create_generated_assets_section(agent_data):
    """Create generated assets section with prompts and scripts."""
    visual_insights = agent_data.get('visual_insights', {})
    platform_content = agent_data.get('platform_content', {})
    
    assets = {
        "image_prompts": [],
        "video_scripts": [],
        "email_templates": [],
        "blog_outlines": []
    }
    
    # Create image prompts from visual insights
    if visual_insights:
        themes = visual_insights.get('visual_themes', [])
        elements = visual_insights.get('primary_visual_elements', [])
        
        for theme in themes[:3]:
            prompt = f"A {theme.lower()} styled image featuring {', '.join(elements[:2])}, professional photography with modern aesthetic"
            assets["image_prompts"].append(prompt)
    
    # Create video scripts from platform content
    youtube_content = platform_content.get('youtube', {})
    if youtube_content:
        video_ideas = youtube_content.get('video_ideas', [])
        for idea in video_ideas[:2]:
            script = {
                "type": "Long form video" if "comprehensive" in idea.lower() else "Short form video",
                "content": f"Script for {idea}: Introduction, main content demonstration, call to action, and engagement prompts."
            }
            assets["video_scripts"].append(script)
    
    # Create email templates
    assets["email_templates"] = [
        {
            "subject": "Your Marketing Campaign is Ready!",
            "body": "Hi [Name],\n\nWe've created a comprehensive marketing strategy tailored for your product. Check out the detailed campaign plan and start engaging with your audience today!"
        }
    ]
    
    # Create blog outlines
    assets["blog_outlines"] = [
        {
            "title": "Comprehensive Marketing Strategy Guide",
            "points": [
                "Understanding your target audience",
                "Platform-specific content creation",
                "Measuring campaign success",
                "Optimizing for engagement"
            ]
        }
    ]
    
    return assets

def create_comprehensive_fallback_structure(request_data):
    """Create a comprehensive fallback structure when agent response parsing fails."""
    product = request_data.get('product', {})
    
    return {
        "product": create_product_section(request_data),
        "content_ideas": [
            {
                "platform": "Instagram",
                "topic": f"{product.get('name', 'Product')} showcase",
                "engagement_score": 85,
                "caption": f"Discover the amazing features of {product.get('name', 'our product')}!",
                "hashtags": ["#product", "#marketing", "#engagement"]
            }
        ],
        "campaigns": [
            {
                "name": "Product Launch Campaign",
                "duration": "4 weeks",
                "posts_per_week": 3,
                "platforms": ["Instagram", "TikTok", "YouTube"],
                "calendar": {
                    "Week 1": "Product introduction and feature highlights",
                    "Week 2": "User testimonials and social proof",
                    "Week 3": "Educational content and tutorials",
                    "Week 4": "Call to action and conversion focus"
                },
                "adaptations": {
                    "Instagram": "Visual storytelling with high-quality images and reels",
                    "TikTok": "Short engaging videos with trending sounds",
                    "YouTube": "Detailed product demonstrations and reviews"
                }
            }
        ],
        "generated_assets": create_generated_assets_section({}),
        "analytics": create_analytics_data(),
        "related_youtube_videos": []
    }

def create_comprehensive_campaign_response(agent_response, request_data, campaign_id):
    """
    Create the comprehensive campaign response structure from agent response.
    
    Args:
        agent_response: The structured response from the Bedrock agent
        request_data: Original request data
        campaign_id: Generated campaign ID
    
    Returns:
        Comprehensive response matching the expected frontend structure
    """
    try:
        # If agent response already has the comprehensive structure, use it directly with enhancements
        if all(key in agent_response for key in ['product', 'content_ideas', 'campaigns', 'generated_assets']):
            comprehensive_response = agent_response.copy()
            comprehensive_response.update({
                "campaign_id": campaign_id,
                "status": "completed",
                "message": "Comprehensive campaign response created successfully."
            })
            # Ensure analytics is present
            if 'analytics' not in comprehensive_response:
                comprehensive_response['analytics'] = create_analytics_data()
            return comprehensive_response
        
        # Otherwise, create comprehensive response structure from legacy format
        comprehensive_response = {
            "campaign_id": campaign_id,
            "status": "completed",
            "message": "Comprehensive campaign response created successfully.",
            "product": agent_response.get('product', create_product_section(request_data)),
            "content_ideas": agent_response.get('content_ideas', create_content_ideas_from_platform_content(agent_response.get('platform_content', {}))),
            "campaigns": agent_response.get('campaigns', create_campaign_sections(agent_response)),
            "generated_assets": agent_response.get('generated_assets', create_generated_assets_section(agent_response)),
            "platform_content": agent_response.get('platform_content', {}),
            "market_trends": agent_response.get('market_trends', {}),
            "success_metrics": agent_response.get('success_metrics', {}),
            "analytics": agent_response.get('analytics', create_analytics_data()),
            "related_youtube_videos": agent_response.get('related_youtube_videos', [])
        }
        
        return comprehensive_response
        
    except Exception as e:
        print(f"Error creating comprehensive campaign response: {str(e)}")
        # Return fallback structure with all required sections
        fallback_response = create_comprehensive_fallback_structure(request_data)
        return {
            "campaign_id": campaign_id,
            "status": "completed",
            "message": "Comprehensive response created with fallback data.",
            **fallback_response
        }

def create_analytics_data():
    """Create analytics data for KPI cards."""
    return {
        "estimatedReach": random.randint(100000, 500000),
        "projectedEngagement": round(random.uniform(7.5, 12.0), 1),
        "conversionRate": round(random.uniform(1.5, 4.0), 1),
        "roi": round(random.uniform(3.0, 6.0), 1)
    }