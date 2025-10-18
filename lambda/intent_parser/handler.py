import json
import boto3
import os
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Intent parser Lambda that orchestrates campaign generation.
    
    Two-tier architecture:
    1. TRY: Invoke Bedrock agent with tool calling enabled
    2. FALLBACK: If agent fails, invoke Lambdas sequentially and aggregate results,
                 then have agent synthesize without tool calling
    
    Input:
    {
        "product_info": {...},
        "s3_info": {...},
        "target_markets": {...},
        "campaign_objectives": {...}
    }
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Validate input
        if not isinstance(event, dict):
            return create_error_response("Invalid request format: expected JSON object")
        
        product_info = event.get('product_info', {})
        s3_info = event.get('s3_info', {})
        target_markets = event.get('target_markets', {})
        campaign_objectives = event.get('campaign_objectives', {})
        
        # Generate correlation ID for tracking
        correlation_id = str(uuid.uuid4())
        print(f"Correlation ID: {correlation_id}")
        
        # TIER 1: Try Bedrock Agent with tool calling
        print("=" * 50)
        print("TIER 1: Attempting Bedrock agent with tool calling")
        print("=" * 50)
        
        agent_result = try_bedrock_agent_with_tools(
            product_info=product_info,
            s3_info=s3_info,
            target_markets=target_markets,
            campaign_objectives=campaign_objectives,
            correlation_id=correlation_id
        )
        
        if agent_result.get('success'):
            print("TIER 1 SUCCESS: Bedrock agent generated campaign")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'correlation_id': correlation_id,
                    'generation_method': 'bedrock_agent_with_tools',
                    'campaign': agent_result.get('campaign')
                })
            }
        
        # TIER 1 FAILED - Log and proceed to TIER 2
        print("\n" + "=" * 50)
        print("TIER 1 FAILED: Bedrock agent did not generate valid campaign")
        print("Reason:", agent_result.get('error', 'Unknown'))
        print("=" * 50)
        print("\nTIER 2: Using fail-safe orchestration")
        print("=" * 50)
        
        # TIER 2: Fail-safe orchestration
        aggregated_data = tier2_fail_safe_orchestration(
            product_info=product_info,
            s3_info=s3_info,
            target_markets=target_markets,
            campaign_objectives=campaign_objectives,
            correlation_id=correlation_id
        )
        
        if not aggregated_data.get('success'):
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'correlation_id': correlation_id,
                    'error': 'Failed to generate campaign data: ' + aggregated_data.get('error', 'Unknown')
                })
            }
        
        product_id = aggregated_data.get('product_id')
        aggregated_record = aggregated_data.get('aggregated_record', {})
        
        # Now invoke Bedrock agent WITHOUT tool calling - just for synthesis
        print("\nTIER 2b: Invoking Bedrock agent for data synthesis (no tool calling)")
        agent_synthesis_result = synthesize_with_bedrock(
            product_id=product_id,
            aggregated_record=aggregated_record,
            campaign_objectives=campaign_objectives,
            correlation_id=correlation_id
        )
        
        if agent_synthesis_result.get('success'):
            print("TIER 2 SUCCESS: Bedrock synthesized campaign from aggregated data")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'correlation_id': correlation_id,
                    'generation_method': 'fail_safe_orchestration_with_synthesis',
                    'product_id': product_id,
                    'campaign': agent_synthesis_result.get('campaign')
                })
            }
        
        # If synthesis also fails, return aggregated data as-is
        print("TIER 2 WARNING: Bedrock synthesis also failed, returning aggregated data")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'correlation_id': correlation_id,
                'generation_method': 'fail_safe_aggregated_data_only',
                'product_id': product_id,
                'campaign': create_fallback_campaign(aggregated_record, campaign_objectives),
                'warning': 'Campaign generated from aggregated data only, Bedrock synthesis unavailable'
            })
        }
        
    except Exception as e:
        print(f"Fatal error in intent parser: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Intent parser failure: {str(e)}'
            })
        }


def try_bedrock_agent_with_tools(product_info, s3_info, target_markets, campaign_objectives, correlation_id):
    """
    Tier 1: Try to invoke Bedrock agent with tool calling enabled.
    
    Returns:
        Dict with 'success' and 'campaign' keys if successful, or 'error' if failed
    """
    try:
        agent_id = os.environ.get('BEDROCK_AGENT_ID', '1MGRL5IMZ2')
        agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'YZRQ8FV4GH')
        session_id = f"session-{correlation_id}"
        
        # Prepare agent input
        prompt = f"""Generate a comprehensive viral marketing campaign based on:

Product Information:
{json.dumps(product_info, indent=2)}

Target Markets: {json.dumps(target_markets, indent=2)}

Campaign Objectives: {json.dumps(campaign_objectives, indent=2)}

Image Location: s3://{s3_info.get('bucket', 'degenerals-mi-dev-images')}/{s3_info.get('key', '')}

Please analyze the product image, enrich the campaign data with market insights and YouTube recommendations, 
and provide cultural intelligence for the target markets. Then synthesize all information into a complete 
marketing campaign strategy with specific tactics for each platform.

Use tool calling to:
1. Analyze the product image
2. Enrich campaign data
3. Analyze cultural insights

Then synthesize the results into a complete campaign JSON."""

        print(f"Invoking Bedrock agent {agent_id} with session {session_id}")
        
        # Invoke Bedrock agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Process response stream
        event_stream = response.get('completion', [])
        agent_response_text = ""
        
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response_text += chunk['bytes'].decode('utf-8')
        
        print(f"Bedrock agent response length: {len(agent_response_text)} chars")
        
        # Try to extract JSON campaign from response
        campaign = extract_campaign_json(agent_response_text)
        
        if campaign:
            print("Successfully extracted campaign JSON from agent response")
            return {
                'success': True,
                'campaign': campaign
            }
        else:
            return {
                'success': False,
                'error': 'Agent did not return valid campaign JSON'
            }
        
    except Exception as e:
        print(f"Bedrock agent invocation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def tier2_fail_safe_orchestration(product_info, s3_info, target_markets, campaign_objectives, correlation_id):
    """
    Tier 2: Invoke Lambdas sequentially and aggregate results.
    
    1. Image analysis Lambda
    2. Data enrichment Lambda
    3. Cultural intelligence Lambda
    4. Read aggregated record from DynamoDB
    
    Returns:
        Dict with 'success', 'product_id', and 'aggregated_record' keys
    """
    try:
        # Step 1: Invoke image analysis Lambda
        print("\nStep 1/3: Invoking image-analysis Lambda")
        image_result = invoke_lambda_sync(
            function_name=os.environ.get('LAMBDA_IMAGE_ANALYSIS', 'degenerals-mi-dev-image-analysis'),
            payload={
                'actionGroup': 'image-analysis',
                'function': 'analyze_product_image',
                'parameters': {
                    'product_info': json.dumps(product_info),
                    's3_info': json.dumps(s3_info)
                }
            }
        )
        
        if not image_result.get('success'):
            return {
                'success': False,
                'error': f"Image analysis failed: {image_result.get('error', 'Unknown')}"
            }
        
        product_id = image_result.get('product_id')
        user_id = image_result.get('user_id', 'anonymous')
        print(f"Image analysis successful, product_id: {product_id}, user_id: {user_id}")
        
        # Step 2: Invoke data enrichment Lambda
        print("\nStep 2/3: Invoking data-enrichment Lambda")
        enrichment_result = invoke_lambda_sync(
            function_name=os.environ.get('LAMBDA_DATA_ENRICHMENT', 'degenerals-mi-dev-data-enrichment'),
            payload={
                'actionGroup': 'data-enrichment',
                'function': 'enrich_campaign_data',
                'parameters': {
                    'product_id': product_id,
                    'user_id': user_id,
                    'campaign_info': json.dumps(campaign_objectives)
                }
            }
        )
        
        if not enrichment_result.get('success'):
            print(f"Data enrichment warning: {enrichment_result.get('error', 'Unknown')}")
            # Don't fail - continue with what we have
        else:
            print("Data enrichment successful")
        
        # Step 3: Invoke cultural intelligence Lambda
        print("\nStep 3/3: Invoking cultural-intelligence Lambda")
        cultural_result = invoke_lambda_sync(
            function_name=os.environ.get('LAMBDA_CULTURAL_INTELLIGENCE', 'degenerals-mi-dev-cultural-intelligence'),
            payload={
                'actionGroup': 'cultural-intelligence',
                'function': 'analyze_cultural_insights',
                'parameters': {
                    'product_id': product_id,
                    'user_id': user_id,
                    'target_markets': json.dumps(target_markets)
                }
            }
        )
        
        if not cultural_result.get('success'):
            print(f"Cultural intelligence warning: {cultural_result.get('error', 'Unknown')}")
            # Don't fail - continue with what we have
        else:
            print("Cultural intelligence successful")
        
        # Ensure user_id is consistent throughout orchestration
        user_id = cultural_result.get('user_id', user_id)
        
        # Step 4: Read aggregated record from DynamoDB
        print("\nStep 4: Reading aggregated record from DynamoDB")
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'products')
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'product_id': product_id, 'user_id': user_id})
        aggregated_record = response.get('Item', {})
        
        if not aggregated_record:
            return {
                'success': False,
                'error': f"Could not retrieve product record {product_id} from DynamoDB"
            }
        
        print(f"Retrieved aggregated record for product {product_id}")
        
        return {
            'success': True,
            'product_id': product_id,
            'aggregated_record': aggregated_record
        }
        
    except Exception as e:
        print(f"Tier 2 orchestration error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


def invoke_lambda_sync(function_name, payload):
    """
    Synchronously invoke a Lambda function and return parsed result.
    
    Args:
        function_name: Lambda function name
        payload: Payload to send to Lambda
        
    Returns:
        Dict with parsed response or error
    """
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        if response.get('StatusCode') != 200:
            return {
                'success': False,
                'error': f"Lambda returned status {response.get('StatusCode')}"
            }
        
        response_payload = json.loads(response.get('Payload', '{}').read())
        
        # Handle both direct returns and wrapped responses
        if isinstance(response_payload, dict):
            if 'body' in response_payload:
                body = json.loads(response_payload['body']) if isinstance(response_payload['body'], str) else response_payload['body']
                return body
            else:
                return response_payload
        
        return response_payload
        
    except Exception as e:
        print(f"Lambda invocation error for {function_name}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def convert_decimals(obj):
    """
    Recursively convert DynamoDB Decimal objects to native Python types.
    
    This is necessary for JSON serialization, as Decimal objects are not
    JSON serializable by default.
    """
    from decimal import Decimal
    
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, Decimal):
        # Convert to int if whole number, otherwise to float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def synthesize_with_bedrock(product_id, aggregated_record, campaign_objectives, correlation_id):
    """
    Invoke Claude 3 Haiku model directly to synthesize campaign from aggregated data.
    
    Uses Bedrock InvokeModel API (not agent) with Claude 3 Haiku for cost-effective synthesis.
    
    Returns:
        Dict with 'success' and 'campaign' keys
    """
    try:
        # Convert DynamoDB Decimals to native Python types for JSON serialization
        clean_record = convert_decimals(aggregated_record)
        clean_objectives = convert_decimals(campaign_objectives)
        
        # Prepare synthesis prompt with complete data
        product_name = clean_record.get('product_name', 'Unknown Product')
        image_labels = clean_record.get('image_labels', [])
        youtube_videos = clean_record.get('youtube_videos', [])
        market_insights = clean_record.get('market_insights', {})
        
        prompt = f"""You are a viral marketing campaign expert. Based on the complete market analysis data provided, synthesize a comprehensive marketing campaign strategy.

Product: {product_name}
Product ID: {product_id}

Image Analysis (Product Features Detected):
{json.dumps(image_labels[:5], indent=2)}

YouTube Video Recommendations & Trends:
{json.dumps(youtube_videos, indent=2)}

Market Insights by Region:
{json.dumps(market_insights, indent=2)}

Campaign Objectives & Constraints:
{json.dumps(clean_objectives, indent=2)}

Create a complete marketing campaign strategy with:
1. Campaign theme and compelling messaging
2. Platform-specific content strategies (Instagram, TikTok, YouTube, LinkedIn)
3. Content calendar with key milestones
4. Target audience segmentation and personas
5. Expected KPIs and success metrics
6. Budget allocation across platforms

Return ONLY valid JSON with the campaign details. No additional text."""

        print(f"Invoking Amazon Nova Pro model for campaign synthesis")
        
        # Create Bedrock runtime client for model invocation
        bedrock_client = boto3.client('bedrock-runtime')
        
        # Invoke Amazon Nova Pro model directly using inference profile ARN
        # Nova uses a different request format than Claude
        response = bedrock_client.invoke_model(
            modelId='arn:aws:bedrock:eu-west-1::inference-profile/eu.amazon.nova-pro-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'messages': [
                    {
                        'role': 'user',
                        'content': [{'text': prompt}]
                    }
                ],
                'inferenceConfig': {
                    'maxTokens': 2048
                }
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        # Amazon Nova Pro response format: response_body['output']['message']['content'][0]['text']
        model_response_text = response_body['output']['message']['content'][0]['text']
        
        print(f"Amazon Nova Pro response length: {len(model_response_text)} chars")
        
        # Try to extract JSON campaign from response
        campaign = extract_campaign_json(model_response_text)
        
        if campaign:
            print("Successfully extracted campaign JSON from model response")
            return {
                'success': True,
                'campaign': campaign
            }
        else:
            print("Could not extract valid campaign JSON from response")
            print(f"Response text: {model_response_text[:500]}")
            return {
                'success': False,
                'error': 'Model did not produce valid campaign JSON'
            }
        
    except Exception as e:
        print(f"Bedrock model synthesis failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


def extract_campaign_json(response_text):
    """
    Extract valid campaign JSON from agent response text.
    
    Tries to find JSON object in response, validating it has campaign-like structure.
    """
    try:
        # Try direct JSON parse
        data = json.loads(response_text)
        if is_valid_campaign(data):
            return data
    except:
        pass
    
    # Try to find JSON object in text
    import re
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if is_valid_campaign(data):
                return data
        except:
            pass
    
    return None


def is_valid_campaign(obj):
    """Check if object looks like a valid campaign."""
    if not isinstance(obj, dict):
        return False
    
    # Should have at least one of these keys
    campaign_keys = ['campaign', 'strategy', 'plan', 'theme', 'messaging']
    return any(key in obj for key in campaign_keys) or len(obj) > 3


def create_fallback_campaign(aggregated_record, campaign_objectives):
    """Create a basic campaign structure from aggregated data."""
    product_name = aggregated_record.get('product_name', 'Product')
    image_labels = aggregated_record.get('image_labels', [])[:3]
    
    return {
        'campaign_name': f"{product_name} Viral Marketing Campaign",
        'theme': f"Showcase the {product_name} and its unique features",
        'platforms': ['Instagram', 'TikTok', 'YouTube'],
        'target_audience': campaign_objectives.get('target_audience', 'General'),
        'key_messaging': f"Discover the innovation in {product_name}",
        'product_highlights': [label.get('name', '') for label in image_labels if isinstance(label, dict)],
        'timeline': '30 days',
        'estimated_reach': 'Up to 1M users'
    }


def create_error_response(error_message):
    """Create an error response."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }
