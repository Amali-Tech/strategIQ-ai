import json
import boto3
import os
import uuid
import traceback
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Initialize AWS clients
bedrock_agent_client = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for cultural intelligence queries using Bedrock Knowledge Bases.
    Provides cross-cultural adaptation insights and market-specific intelligence.
    
    Handles both direct invocation and Bedrock agent invocation formats.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check if this is a Bedrock agent invocation
        if 'messageVersion' in event and 'requestBody' in event:
            return handle_bedrock_agent_invocation(event, context)
        
        # Handle direct invocation format
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
        
        if function_name == 'get_cultural_insights':
            return handle_cultural_insights(parameters, context)
        elif function_name == 'get_market_intelligence':
            return handle_market_intelligence(parameters, context)
        elif function_name == 'adapt_campaign_content':
            return handle_content_adaptation(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return create_error_response(f"Lambda execution failed: {str(e)}")

def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        api_path = event.get('apiPath', '')
        function_name = event.get('function', '')
        
        # Extract parameters from Bedrock request body
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        
        # Parse the request body content
        json_body = None
        if 'application/json' in content and isinstance(content['application/json'], dict):
            app_json = content['application/json']
            if 'properties' in app_json:
                # Convert properties array to proper JSON structure
                json_body = {}
                for prop in app_json['properties']:
                    prop_name = prop.get('name')
                    prop_value = prop.get('value', '')
                    json_body[prop_name] = prop_value
        
        if not json_body:
            return create_bedrock_error_response("Could not extract valid JSON from Bedrock request", api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body, default=str)}")
        
        if function_name == 'get_cultural_insights' or api_path == '/cultural-insights':
            result = handle_cultural_insights(json_body, context)
        elif function_name == 'get_market_intelligence' or api_path == '/market-intelligence':
            result = handle_market_intelligence(json_body, context)
        elif function_name == 'adapt_campaign_content' or api_path == '/adapt-content':
            result = handle_content_adaptation(json_body, context)
        else:
            return create_bedrock_error_response(f"Unknown function: {function_name}, path: {api_path}", api_path)
        
        # Convert response to Bedrock format
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
            
    except Exception as e:
        print(f"Error in handle_bedrock_agent_invocation: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return create_bedrock_error_response(f"Processing error: {str(e)}", api_path)

def handle_cultural_insights(parameters, context):
    """Get cultural insights from the cultural intelligence knowledge base."""
    try:
        # Extract parameters
        product_id = parameters.get('product_id', '')
        user_id = parameters.get('user_id', 'anonymous')
        target_markets = parameters.get('target_markets', [])
        campaign_type = parameters.get('campaign_type', 'general')
        product_category = parameters.get('product_category', '')
        
        if not product_id:
            return create_error_response("product_id parameter is required")
        if not target_markets:
            return create_error_response("target_markets parameter is required")
        
        # Construct query for cultural knowledge base
        query = f"Cultural adaptation guidelines for {campaign_type} campaign in {', '.join(target_markets)} markets for {product_category} products"
        
        # Query the cultural intelligence knowledge base
        kb_id = get_knowledge_base_id()
        cultural_insights = query_knowledge_base(kb_id, query)
        
        # Create cultural insights data
        insights_data = {
            'target_markets': target_markets,
            'campaign_type': campaign_type,
            'product_category': product_category,
            'cultural_insights': cultural_insights,
            'query_used': query,
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id
        }
        
        # Save to products table
        table_name = "products"  # Use the products table
        save_cultural_insights_to_products(table_name, product_id, user_id, insights_data)
        
        # Return structured response
        return create_success_response({
            'product_id': product_id,
            'user_id': user_id,
            'target_markets': target_markets,
            'cultural_guidelines': parse_cultural_guidelines(cultural_insights),
            'adaptation_recommendations': generate_adaptation_recommendations(cultural_insights, target_markets),
            'cultural_considerations': extract_cultural_considerations(cultural_insights),
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': insights_data['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_cultural_insights: {str(e)}")
        return create_error_response(f"Cultural insights query failed: {str(e)}")

def handle_market_intelligence(parameters, context):
    """Get market-specific intelligence from the market intelligence knowledge base."""
    try:
        # Extract parameters
        product_id = parameters.get('product_id', '')
        user_id = parameters.get('user_id', 'anonymous')
        target_market = parameters.get('target_market', '')
        intelligence_type = parameters.get('intelligence_type', 'general')
        focus_areas = parameters.get('focus_areas', [])
        
        if not product_id:
            return create_error_response("product_id parameter is required")
        if not target_market:
            return create_error_response("target_market parameter is required")
        
        # Construct query for market knowledge base
        focus_query = f" focusing on {', '.join(focus_areas)}" if focus_areas else ""
        query = f"{intelligence_type} market intelligence for {target_market}{focus_query}"
        
        # Query the cultural intelligence knowledge base (same as market intelligence)
        kb_id = get_knowledge_base_id()
        market_intelligence = query_knowledge_base(kb_id, query)
        
        # Create market intelligence data
        intelligence_data = {
            'target_market': target_market,
            'intelligence_type': intelligence_type,
            'focus_areas': focus_areas,
            'market_intelligence': market_intelligence,
            'query_used': query,
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id
        }
        
        # Save to products table
        table_name = "products"
        save_market_intelligence_to_products(table_name, product_id, user_id, intelligence_data)
        
        # Return structured response
        return create_success_response({
            'product_id': product_id,
            'user_id': user_id,
            'target_market': target_market,
            'market_insights': parse_market_insights(market_intelligence),
            'demographic_data': extract_demographic_data(market_intelligence),
            'cultural_preferences': extract_cultural_preferences(market_intelligence),
            'platform_preferences': extract_platform_preferences(market_intelligence),
            'seasonal_considerations': extract_seasonal_data(market_intelligence),
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': intelligence_data['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_market_intelligence: {str(e)}")
        return create_error_response(f"Market intelligence query failed: {str(e)}")

def handle_content_adaptation(parameters, context):
    """Adapt campaign content based on cultural and market intelligence."""
    try:
        # Extract parameters
        product_id = parameters.get('product_id', '')
        user_id = parameters.get('user_id', 'anonymous')
        content = parameters.get('content', {})
        target_markets = parameters.get('target_markets', [])
        content_type = parameters.get('content_type', 'general')
        
        if not product_id:
            return create_error_response("product_id parameter is required")
        if not content or not target_markets:
            return create_error_response("content and target_markets parameters are required")
        
        adaptations = {}
        
        for market in target_markets:
            # Query knowledge base for comprehensive adaptation
            cultural_query = f"Cultural adaptation guidelines for {content_type} content in {market}"
            market_query = f"Market-specific preferences for {content_type} content in {market}"
            
            kb_id = get_knowledge_base_id()
            
            cultural_guidelines = query_knowledge_base(kb_id, cultural_query)
            market_preferences = query_knowledge_base(kb_id, market_query)
            
            # Generate adaptation recommendations
            adaptations[market] = {
                'cultural_adaptations': generate_cultural_adaptations(content, cultural_guidelines),
                'market_optimizations': generate_market_optimizations(content, market_preferences),
                'localization_requirements': extract_localization_requirements(cultural_guidelines, market_preferences),
                'risk_considerations': identify_cultural_risks(cultural_guidelines),
                'platform_adjustments': suggest_platform_adjustments(market_preferences)
            }
        
        # Create adaptation data
        adaptation_data = {
            'original_content': content,
            'target_markets': target_markets,
            'content_type': content_type,
            'adaptations': adaptations,
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id
        }
        
        # Save to products table
        table_name = "products"
        save_content_adaptation_to_products(table_name, product_id, user_id, adaptation_data)
        
        # Return structured response
        return create_success_response({
            'product_id': product_id,
            'user_id': user_id,
            'original_content': content,
            'target_markets': target_markets,
            'market_adaptations': adaptations,
            'global_recommendations': generate_global_recommendations(adaptations),
            'implementation_priority': rank_adaptation_priority(adaptations),
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': adaptation_data['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_content_adaptation: {str(e)}")
        return create_error_response(f"Content adaptation failed: {str(e)}")

def query_knowledge_base(knowledge_base_id, query):
    """Query a Bedrock knowledge base."""
    try:
        response = bedrock_agent_client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 10
                }
            }
        )
        
        # Extract and combine relevant results
        results = []
        for result in response.get('retrievalResults', []):
            results.append({
                'content': result.get('content', {}).get('text', ''),
                'score': result.get('score', 0),
                'metadata': result.get('metadata', {})
            })
        
        return results
        
    except Exception as e:
        print(f"Error querying knowledge base {knowledge_base_id}: {str(e)}")
        return []

# Helper functions for parsing and processing knowledge base results

def parse_cultural_guidelines(cultural_insights):
    """Parse cultural guidelines from knowledge base results."""
    guidelines = []
    for insight in cultural_insights:
        content = insight.get('content', '')
        if any(keyword in content.lower() for keyword in ['guideline', 'recommendation', 'consider', 'avoid']):
            guidelines.append({
                'guideline': content[:200] + '...' if len(content) > 200 else content,
                'confidence': insight.get('score', 0),
                'source': insight.get('metadata', {}).get('source', 'knowledge_base')
            })
    return guidelines[:5]  # Top 5 guidelines

def generate_adaptation_recommendations(cultural_insights, target_markets):
    """Generate adaptation recommendations based on cultural insights."""
    recommendations = []
    
    for market in target_markets:
        market_insights = [i for i in cultural_insights if market.lower() in i.get('content', '').lower()]
        if market_insights:
            top_insight = market_insights[0]
            recommendations.append({
                'market': market,
                'recommendation': f"Adapt content considering {market} cultural values",
                'details': top_insight.get('content', '')[:300] + '...',
                'priority': 'high' if top_insight.get('score', 0) > 0.8 else 'medium'
            })
    
    return recommendations

def extract_cultural_considerations(cultural_insights):
    """Extract key cultural considerations."""
    considerations = []
    keywords = ['religion', 'tradition', 'holiday', 'color', 'symbol', 'gesture', 'taboo']
    
    for insight in cultural_insights:
        content = insight.get('content', '').lower()
        for keyword in keywords:
            if keyword in content:
                considerations.append({
                    'category': keyword,
                    'consideration': insight.get('content', '')[:150] + '...',
                    'importance': 'high' if insight.get('score', 0) > 0.8 else 'medium'
                })
                break
    
    return considerations[:8]  # Top 8 considerations

def parse_market_insights(market_intelligence):
    """Parse market insights from knowledge base results."""
    insights = []
    for intel in market_intelligence:
        content = intel.get('content', '')
        insights.append({
            'insight': content[:250] + '...' if len(content) > 250 else content,
            'relevance': intel.get('score', 0),
            'category': categorize_insight(content)
        })
    return insights[:6]  # Top 6 insights

def extract_demographic_data(market_intelligence):
    """Extract demographic information."""
    demographics = {}
    for intel in market_intelligence:
        content = intel.get('content', '').lower()
        if any(keyword in content for keyword in ['age', 'demographic', 'population', 'income']):
            demographics['summary'] = intel.get('content', '')[:200] + '...'
            break
    return demographics

def extract_cultural_preferences(market_intelligence):
    """Extract cultural preferences."""
    preferences = []
    for intel in market_intelligence:
        content = intel.get('content', '').lower()
        if any(keyword in content for keyword in ['prefer', 'like', 'favor', 'value']):
            preferences.append({
                'preference': intel.get('content', '')[:150] + '...',
                'strength': 'high' if intel.get('score', 0) > 0.8 else 'medium'
            })
    return preferences[:4]

def extract_platform_preferences(market_intelligence):
    """Extract social media platform preferences."""
    platforms = {}
    platform_names = ['facebook', 'instagram', 'tiktok', 'youtube', 'twitter', 'linkedin', 'whatsapp']
    
    for intel in market_intelligence:
        content = intel.get('content', '').lower()
        for platform in platform_names:
            if platform in content:
                platforms[platform] = {
                    'usage': 'high' if intel.get('score', 0) > 0.7 else 'medium',
                    'notes': intel.get('content', '')[:100] + '...'
                }
    
    return platforms

def extract_seasonal_data(market_intelligence):
    """Extract seasonal and holiday information."""
    seasonal = []
    for intel in market_intelligence:
        content = intel.get('content', '').lower()
        if any(keyword in content for keyword in ['holiday', 'season', 'festival', 'celebration']):
            seasonal.append({
                'event': intel.get('content', '')[:120] + '...',
                'relevance': intel.get('score', 0)
            })
    return seasonal[:3]

def categorize_insight(content):
    """Categorize market insight content."""
    content_lower = content.lower()
    if any(keyword in content_lower for keyword in ['social', 'media', 'platform']):
        return 'social_media'
    elif any(keyword in content_lower for keyword in ['culture', 'tradition', 'value']):
        return 'cultural'
    elif any(keyword in content_lower for keyword in ['demographic', 'age', 'population']):
        return 'demographic'
    elif any(keyword in content_lower for keyword in ['economic', 'income', 'spending']):
        return 'economic'
    else:
        return 'general'

def generate_cultural_adaptations(content, cultural_guidelines):
    """Generate cultural adaptations for content."""
    adaptations = []
    
    # Analyze content elements that might need cultural adaptation
    content_text = str(content)
    
    for guideline in cultural_guidelines:
        guideline_content = guideline.get('content', '')
        if any(keyword in guideline_content.lower() for keyword in ['color', 'image', 'text', 'message']):
            adaptations.append({
                'element': 'visual_content',
                'adaptation': guideline_content[:150] + '...',
                'priority': 'high' if guideline.get('score', 0) > 0.8 else 'medium'
            })
    
    return adaptations[:3]

def generate_market_optimizations(content, market_preferences):
    """Generate market-specific optimizations."""
    optimizations = []
    
    for preference in market_preferences:
        pref_content = preference.get('content', '')
        optimizations.append({
            'optimization_type': 'platform_specific',
            'description': pref_content[:150] + '...',
            'impact': 'high' if preference.get('score', 0) > 0.8 else 'medium'
        })
    
    return optimizations[:3]

def extract_localization_requirements(cultural_guidelines, market_preferences):
    """Extract localization requirements."""
    requirements = []
    
    all_guidelines = cultural_guidelines + market_preferences
    for guideline in all_guidelines:
        content = guideline.get('content', '').lower()
        if any(keyword in content for keyword in ['translate', 'language', 'local', 'adapt']):
            requirements.append({
                'requirement': guideline.get('content', '')[:120] + '...',
                'category': 'language' if 'language' in content else 'cultural'
            })
    
    return requirements[:4]

def identify_cultural_risks(cultural_guidelines):
    """Identify potential cultural risks."""
    risks = []
    
    for guideline in cultural_guidelines:
        content = guideline.get('content', '').lower()
        if any(keyword in content for keyword in ['avoid', 'risk', 'sensitive', 'inappropriate', 'taboo']):
            risks.append({
                'risk': guideline.get('content', '')[:150] + '...',
                'severity': 'high' if guideline.get('score', 0) > 0.8 else 'medium'
            })
    
    return risks[:3]

def suggest_platform_adjustments(market_preferences):
    """Suggest platform-specific adjustments."""
    adjustments = []
    
    for preference in market_preferences:
        content = preference.get('content', '').lower()
        if any(keyword in content for keyword in ['platform', 'social', 'media', 'post']):
            adjustments.append({
                'platform_adjustment': preference.get('content', '')[:120] + '...',
                'importance': 'high' if preference.get('score', 0) > 0.8 else 'medium'
            })
    
    return adjustments[:3]

def generate_global_recommendations(adaptations):
    """Generate global recommendations across all markets."""
    recommendations = []
    
    # Analyze common themes across all market adaptations
    all_adaptations = []
    for market, adaptation in adaptations.items():
        all_adaptations.extend(adaptation.get('cultural_adaptations', []))
    
    # Group common recommendations
    if all_adaptations:
        recommendations.append({
            'recommendation': 'Implement consistent cultural sensitivity review process',
            'rationale': 'Multiple markets require cultural adaptations',
            'priority': 'high'
        })
    
    return recommendations

def rank_adaptation_priority(adaptations):
    """Rank adaptation priorities across markets."""
    priorities = []
    
    for market, adaptation in adaptations.items():
        high_priority_count = sum(1 for item in adaptation.get('cultural_adaptations', []) if item.get('priority') == 'high')
        priorities.append({
            'market': market,
            'priority_score': high_priority_count,
            'urgency': 'high' if high_priority_count > 2 else 'medium'
        })
    
    return sorted(priorities, key=lambda x: x['priority_score'], reverse=True)

# DynamoDB and utility functions

def convert_floats_to_decimals(obj):
    """Convert all float values in a nested object to Decimal for DynamoDB compatibility."""
    if isinstance(obj, list):
        return [convert_floats_to_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def save_cultural_insights_to_products(table_name, product_id, user_id, insights_data):
    """Save or update cultural insights in the products table."""
    try:
        table = dynamodb.Table(table_name)
        
        # Convert floats to Decimals for DynamoDB compatibility
        insights_data = convert_floats_to_decimals(insights_data)
        
        # Check if product record exists
        try:
            response = table.get_item(Key={'product_id': product_id, 'user_id': user_id})
            existing_item = response.get('Item')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                # Table might not exist or wrong key structure
                raise Exception(f"Products table validation error: {e.response['Error']['Message']}")
            raise
        
        if existing_item:
            # Update existing record with cultural insights
            update_expression = "SET cultural_insights = :insights, updated_at = :updated_at"
            expression_values = {
                ':insights': insights_data,
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            table.update_item(
                Key={'product_id': product_id, 'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            print(f"Updated cultural insights for product {product_id}")
        else:
            # Create new product record with cultural insights
            new_record = {
                'product_id': product_id,
                'user_id': user_id,
                'cultural_insights': insights_data,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=new_record)
            print(f"Created new product record {product_id} with cultural insights")
            
    except Exception as e:
        print(f"Error saving cultural insights to products table: {str(e)}")
        raise

def save_market_intelligence_to_products(table_name, product_id, user_id, intelligence_data):
    """Save or update market intelligence in the products table."""
    try:
        table = dynamodb.Table(table_name)
        
        # Convert floats to Decimals for DynamoDB compatibility
        intelligence_data = convert_floats_to_decimals(intelligence_data)
        
        # Check if product record exists
        try:
            response = table.get_item(Key={'product_id': product_id, 'user_id': user_id})
            existing_item = response.get('Item')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                # Table might not exist or wrong key structure
                raise Exception(f"Products table validation error: {e.response['Error']['Message']}")
            raise
        
        if existing_item:
            # Update existing record with market intelligence
            update_expression = "SET market_intelligence = :intelligence, updated_at = :updated_at"
            expression_values = {
                ':intelligence': intelligence_data,
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            table.update_item(
                Key={'product_id': product_id, 'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            print(f"Updated market intelligence for product {product_id}")
        else:
            # Create new product record with market intelligence
            new_record = {
                'product_id': product_id,
                'user_id': user_id,
                'market_intelligence': intelligence_data,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=new_record)
            print(f"Created new product record {product_id} with market intelligence")
            
    except Exception as e:
        print(f"Error saving market intelligence to products table: {str(e)}")
        raise

def save_content_adaptation_to_products(table_name, product_id, user_id, adaptation_data):
    """Save or update content adaptation in the products table."""
    try:
        table = dynamodb.Table(table_name)
        
        # Convert floats to Decimals for DynamoDB compatibility
        adaptation_data = convert_floats_to_decimals(adaptation_data)
        
        # Check if product record exists
        try:
            response = table.get_item(Key={'product_id': product_id, 'user_id': user_id})
            existing_item = response.get('Item')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                # Table might not exist or wrong key structure
                raise Exception(f"Products table validation error: {e.response['Error']['Message']}")
            raise
        
        if existing_item:
            # Update existing record with content adaptation
            update_expression = "SET content_adaptation = :adaptation, updated_at = :updated_at"
            expression_values = {
                ':adaptation': adaptation_data,
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            table.update_item(
                Key={'product_id': product_id, 'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            print(f"Updated content adaptation for product {product_id}")
        else:
            # Create new product record with content adaptation
            new_record = {
                'product_id': product_id,
                'user_id': user_id,
                'content_adaptation': adaptation_data,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=new_record)
            print(f"Created new product record {product_id} with content adaptation")
            
    except Exception as e:
        print(f"Error saving content adaptation to products table: {str(e)}")
        raise

def get_knowledge_base_id():
    """Get Knowledge Base ID from environment variables."""
    import os
    # Try multiple environment variable names for backward compatibility
    kb_id = (os.environ.get('CULTURAL_INTELLIGENCE_KB_ID') or 
             os.environ.get('CULTURAL_KB_ID') or 
             os.environ.get('MARKET_KB_ID'))
    
    if not kb_id:
        raise Exception("Knowledge Base ID environment variable not set. Expected CULTURAL_INTELLIGENCE_KB_ID, CULTURAL_KB_ID, or MARKET_KB_ID")
    
    print(f"Using Knowledge Base ID: {kb_id}")
    return kb_id

def get_dynamodb_table_name():
    """Get DynamoDB table name from environment variables."""
    import os
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    if not table_name:
        raise Exception("DYNAMODB_TABLE_NAME environment variable not set")
    return table_name

def create_success_response(data):
    """Create a successful response for Bedrock agent."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'data': data
        })
    }

def create_error_response(error_message):
    """Create an error response for Bedrock agent."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }

def create_bedrock_error_response(error_message, api_path='unknown'):
    """Create a Bedrock-formatted error response."""
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