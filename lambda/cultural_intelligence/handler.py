import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for cultural intelligence and insights.
    
    Can be invoked by:
    1. Bedrock agent (action group) - Returns Bedrock format response with product_id
    2. Intent parser Lambda - Returns JSON response with product_id
    
    Accepts product_id and enriches existing product record with cultural insights.
    Updates DynamoDB record with cultural_status='culturally_enriched'
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check if this is a Bedrock agent invocation
        if 'messageVersion' in event and 'requestBody' in event:
            return handle_bedrock_agent_invocation(event, context)
        
        # Handle direct invocation from intent parser
        action_group = event.get('actionGroup')
        function_name = event.get('function')
        parameters = event.get('parameters', {})
        
        # Convert Bedrock parameter format (list of dicts) to dict format
        if isinstance(parameters, list):
            param_dict = {}
            for param in parameters:
                if isinstance(param, dict) and 'name' in param and 'value' in param:
                    param_dict[param['name']] = param['value']
            parameters = param_dict
        
        if action_group != 'cultural-intelligence':
            return create_error_response(f"Invalid action group: {action_group}")
        
        if function_name == 'analyze_cultural_insights':
            return handle_cultural_intelligence(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_error_response(f"Internal error: {str(e)}")


def handle_cultural_intelligence(parameters, context):
    """
    Handle cultural intelligence analysis for a product campaign.
    
    Args:
        parameters: Dictionary containing product_id, user_id and target markets
        context: Lambda context object
        
    Returns:
        Dictionary with cultural insights and product_id
    """
    try:
        # Extract parameters
        product_id = (parameters.get('product_id') or '').strip()
        user_id = (parameters.get('user_id') or 'anonymous').strip()
        target_markets_raw = parameters.get('target_markets', {})
        
        if not product_id:
            return create_error_response("product_id is required")
        
        # Parse target_markets if it's a JSON string
        if isinstance(target_markets_raw, str):
            try:
                target_markets = json.loads(target_markets_raw)
            except json.JSONDecodeError:
                target_markets = {}
        else:
            target_markets = target_markets_raw if isinstance(target_markets_raw, dict) else {}
        
        # Get existing product record from DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'products')
        product_record = get_product_by_id(table_name, product_id, user_id)
        
        if not product_record:
            return create_error_response(f"Product not found: {product_id}")
        
        # Perform cultural intelligence analysis
        cultural_insights = analyze_cultural_context(
            product_name=product_record.get('product_name', 'Unknown'),
            product_category=product_record.get('product_category', ''),
            target_markets=target_markets
        )
        
        # Update the existing product record
        updated_record = update_product_record(
            table_name=table_name,
            product_id=product_id,
            user_id=user_id,
            cultural_insights=cultural_insights,
            request_id=context.aws_request_id
        )
        
        # Return structured response with product_id and user_id
        response_data = {
            'success': True,
            'product_id': product_id,
            'user_id': user_id,
            'cultural_status': 'culturally_enriched',
            'markets_analyzed': len(cultural_insights.get('market_insights', {})),
            'cultural_considerations_count': sum(
                len(v.get('considerations', []))
                for v in cultural_insights.get('market_insights', {}).values()
            ),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error in handle_cultural_intelligence: {str(e)}")
        return create_error_response(f"Cultural intelligence analysis failed: {str(e)}")


def get_product_by_id(table_name, product_id, user_id):
    """
    Retrieve product record from DynamoDB by product_id and user_id.
    
    Args:
        table_name: DynamoDB table name
        product_id: Product ID
        user_id: User ID
        
    Returns:
        Product record or None if not found
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'product_id': product_id, 'user_id': user_id})
        return response.get('Item')
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"DynamoDB error: {error_code} - {error_message}")
        raise


def analyze_cultural_context(product_name, product_category, target_markets):
    """
    Analyze cultural context and provide insights for different markets.
    
    Args:
        product_name: Product name
        product_category: Product category
        target_markets: Dictionary of target markets
        
    Returns:
        Dictionary with cultural insights per market
    """
    markets = target_markets.get('markets', [])
    if isinstance(markets, str):
        try:
            markets = json.loads(markets)
        except:
            markets = ['Global']
    
    if not markets:
        markets = ['Global']
    
    market_insights = {}
    
    for market in markets:
        market_key = str(market).lower().replace(' ', '_')
        market_insights[market_key] = generate_market_insights(
            market=str(market),
            product_name=product_name,
            product_category=product_category
        )
    
    return {
        'market_insights': market_insights,
        'communication_guidelines': generate_communication_guidelines(product_category),
        'cultural_sensitivity_notes': generate_sensitivity_notes(),
        'analyzed_at': datetime.utcnow().isoformat()
    }


def generate_market_insights(market, product_name, product_category):
    """Generate cultural insights for a specific market."""
    # Mock insights - in production, integrate with cultural analytics API
    
    market_data = {
        'Global': {
            'language': 'English',
            'timezone': 'UTC',
            'preferred_platforms': ['Facebook', 'Instagram', 'YouTube'],
            'communication_style': 'professional',
            'considerations': [
                'Universal appeal in marketing',
                'Multilingual support recommended',
                'Time zone optimization for content delivery'
            ],
            'best_posting_times': ['9 AM - 11 AM', '6 PM - 8 PM'],
            'cultural_nuances': 'General Western market assumptions'
        },
        'North America': {
            'language': 'English',
            'timezone': 'America/New_York, America/Los_Angeles',
            'preferred_platforms': ['Instagram', 'TikTok', 'YouTube'],
            'communication_style': 'casual, humor-focused',
            'considerations': [
                'Direct calls to action work well',
                'User-generated content highly valued',
                'Emphasis on individual success stories'
            ],
            'best_posting_times': ['12 PM - 1 PM', '7 PM - 9 PM'],
            'cultural_nuances': 'Fast-paced, trend-driven market'
        },
        'Europe': {
            'language': 'Multiple (English, German, French, etc.)',
            'timezone': 'Europe/London, Europe/Berlin, Europe/Paris',
            'preferred_platforms': ['Instagram', 'Facebook', 'TikTok'],
            'communication_style': 'sophisticated, value-driven',
            'considerations': [
                'Privacy and data protection important',
                'GDPR compliance essential',
                'Quality over quantity in content',
                'Sustainability messaging resonates'
            ],
            'best_posting_times': ['10 AM - 12 PM', '6 PM - 8 PM'],
            'cultural_nuances': 'Quality-conscious, data privacy aware'
        },
        'Asia': {
            'language': 'Multiple (Chinese, Japanese, Hindi, etc.)',
            'timezone': 'Asia/Shanghai, Asia/Tokyo, Asia/Hong_Kong',
            'preferred_platforms': ['WeChat', 'Douyin', 'Instagram'],
            'communication_style': 'aspirational, community-focused',
            'considerations': [
                'Mobile-first consumption',
                'Live streaming highly popular',
                'Influencer partnerships crucial',
                'Localisation essential, not just translation',
                'Lucky numbers and color symbolism important'
            ],
            'best_posting_times': ['7 AM - 9 AM', '9 PM - 11 PM'],
            'cultural_nuances': 'Fast-growing, mobile-dominant market'
        },
        'Latin America': {
            'language': 'Spanish, Portuguese',
            'timezone': 'America/Mexico_City, America/Buenos_Aires',
            'preferred_platforms': ['Instagram', 'TikTok', 'Facebook'],
            'communication_style': 'warm, family-oriented, festive',
            'considerations': [
                'Family values important in messaging',
                'Celebration and festivity resonate',
                'Spanish language nuances vary by country',
                'Music and visual storytelling key'
            ],
            'best_posting_times': ['11 AM - 1 PM', '8 PM - 10 PM'],
            'cultural_nuances': 'Relationship-driven, festive market'
        }
    }
    
    # Get market-specific data or use Global as default
    insights = market_data.get(market, market_data['Global']).copy()
    insights['market'] = market
    insights['product_category_relevance'] = f"{product_name} in {market} market"
    
    return insights


def generate_communication_guidelines(product_category):
    """Generate communication guidelines for the product category."""
    category_guidelines = {
        'electronics': {
            'tone': 'Tech-savvy, innovative',
            'focus': ['Performance', 'Innovation', 'Durability'],
            'avoid': ['Overstated claims', 'Technical jargon for general audience'],
            'storytelling_angle': 'Innovation changing lives'
        },
        'fashion': {
            'tone': 'Aspirational, trendy',
            'focus': ['Style', 'Quality', 'Self-expression'],
            'avoid': ['Unsustainable messaging', 'Unrealistic body standards'],
            'storytelling_angle': 'Expressing individuality'
        },
        'food': {
            'tone': 'Warm, sensory-rich',
            'focus': ['Quality', 'Taste', 'Experience'],
            'avoid': ['Health claims without evidence', 'Cultural appropriation'],
            'storytelling_angle': 'Creating shared experiences'
        },
        'health': {
            'tone': 'Trustworthy, evidence-based',
            'focus': ['Wellness', 'Science', 'Personal care'],
            'avoid': ['Medical claims without disclaimer', 'Overpromising'],
            'storytelling_angle': 'Empowering better choices'
        }
    }
    
    category = product_category.lower() if product_category else 'electronics'
    return category_guidelines.get(category, category_guidelines['electronics'])


def generate_sensitivity_notes():
    """Generate general cultural sensitivity notes."""
    return [
        'Always research local holidays and avoid insensitive timing',
        'Use diverse representation in visual content',
        'Respect local customs around food, religion, and traditions',
        'Ensure color symbolism is culturally appropriate',
        'Test messaging with local cultural experts',
        'Be aware of gender roles and family structures in target markets',
        'Consider local environmental and social values',
        'Avoid stereotypes and clichés about cultures'
    ]


def update_product_record(table_name, product_id, user_id, cultural_insights, request_id):
    """
    Update existing product record in DynamoDB with cultural intelligence data.
    
    Args:
        table_name: DynamoDB table name
        product_id: Product ID
        user_id: User ID
        cultural_insights: Results from cultural analysis
        request_id: Lambda request ID
        
    Returns:
        Updated product record
    """
    try:
        from decimal import Decimal
        
        # Convert float values to Decimal for DynamoDB compatibility
        def convert_floats(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(v) for v in obj]
            return obj
        
        timestamp = datetime.utcnow().isoformat()
        
        table = dynamodb.Table(table_name)
        
        # Update the record with cultural insights
        response = table.update_item(
            Key={
                'product_id': product_id,
                'user_id': user_id
            },
            UpdateExpression="""
                SET market_insights = :market_insights,
                    communication_guidelines = :guidelines,
                    cultural_sensitivity_notes = :sensitivity,
                    cultural_status = :status,
                    updated_at = :timestamp,
                    cultural_request_id = :request_id
            """,
            ExpressionAttributeValues={
                ':market_insights': convert_floats(cultural_insights['market_insights']),
                ':guidelines': convert_floats(cultural_insights['communication_guidelines']),
                ':sensitivity': cultural_insights['cultural_sensitivity_notes'],
                ':status': 'culturally_enriched',
                ':timestamp': timestamp,
                ':request_id': request_id
            },
            ReturnValues='ALL_NEW'
        )
        
        print(f"Successfully updated product record {product_id} with cultural insights")
        return response.get('Attributes', {})
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"DynamoDB error: {error_code} - {error_message}")
        raise Exception(f"Failed to update product in DynamoDB: {error_message}")


def create_error_response(error_message):
    """Create an error response."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }


def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        
        function_name = event.get('function', '')
        api_path = event.get('apiPath', '')
        
        print(f"Bedrock invocation - Function: {function_name}, API Path: {api_path}")
        
        # Parse properties array
        json_body = {}
        if 'application/json' in content and isinstance(content['application/json'], dict):
            app_json = content['application/json']
            if 'properties' in app_json:
                for prop in app_json['properties']:
                    prop_name = prop.get('name')
                    prop_value = prop.get('value', '')
                    
                    if prop_name == 'product_id':
                        json_body['product_id'] = prop_value
                    
                    elif prop_name == 'target_markets':
                        try:
                            json_body['target_markets'] = json.loads(prop_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid target_markets JSON", api_path)
        
        if not json_body.get('product_id'):
            return create_bedrock_error_response("product_id is required", api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body)}")
        
        if function_name == 'analyze_cultural_insights' or api_path == '/analyze-cultural-insights':
            result = handle_cultural_intelligence(json_body, context)
            
            if result.get('statusCode') == 200:
                body_data = json.loads(result['body'])
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': 'cultural-intelligence',
                        'apiPath': api_path,
                        'httpMethod': 'POST',
                        'httpStatusCode': 200,
                        'responseBody': {
                            'application/json': {
                                'body': json.dumps(body_data)
                            }
                        }
                    }
                }
            else:
                error_data = json.loads(result['body'])
                return create_bedrock_error_response(error_data.get('error', 'Unknown error'), api_path)
        else:
            return create_bedrock_error_response(f"Unknown function: {function_name}", api_path)
            
    except Exception as e:
        print(f"Error in handle_bedrock_agent_invocation: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return create_bedrock_error_response(f"Internal error: {str(e)}", "/analyze-cultural-insights")


def create_bedrock_error_response(error_message, api_path='/analyze-cultural-insights'):
    """Create a Bedrock agent compatible error response."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'cultural-intelligence',
            'apiPath': api_path,
            'httpMethod': 'POST',
            'httpStatusCode': 400,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'success': False,
                        'error': error_message
                    })
                }
            }
        }
    }
