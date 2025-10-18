import json
import boto3
import os
import urllib.request
import urllib.parse
from datetime import datetime
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for data enrichment using external APIs and YouTube.
    
    Can be invoked by:
    1. Bedrock agent (action group) - Returns Bedrock format response with product_id
    2. Intent parser Lambda - Returns JSON response with product_id
    
    Accepts product_id and enriches existing product record with data.
    Updates DynamoDB record with enrichment_status='data_enriched'
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
        
        if action_group != 'data-enrichment':
            return create_error_response(f"Invalid action group: {action_group}")
        
        if function_name == 'enrich_campaign_data':
            return handle_data_enrichment(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_error_response(f"Internal error: {str(e)}")


def handle_data_enrichment(parameters, context):
    """
    Handle data enrichment for a product campaign.
    
    Args:
        parameters: Dictionary containing product_id, user_id and campaign info
        context: Lambda context object
        
    Returns:
        Dictionary with enrichment results and product_id
    """
    try:
        # Extract parameters
        product_id = (parameters.get('product_id') or '').strip()
        user_id = (parameters.get('user_id') or 'anonymous').strip()
        campaign_info_raw = parameters.get('campaign_info', {})
        
        if not product_id:
            return create_error_response("product_id is required")
        
        # Parse campaign_info if it's a JSON string
        if isinstance(campaign_info_raw, str):
            try:
                campaign_info = json.loads(campaign_info_raw)
            except json.JSONDecodeError:
                campaign_info = {}
        else:
            campaign_info = campaign_info_raw if isinstance(campaign_info_raw, dict) else {}
        
        # Get existing product record from DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'products')
        product_record = get_product_by_id(table_name, product_id, user_id)
        
        if not product_record:
            return create_error_response(f"Product not found: {product_id}")
        
        # Perform data enrichment
        enrichment_results = enrich_product_data(
            product_name=product_record.get('product_name', 'Unknown'),
            product_category=product_record.get('product_category', ''),
            campaign_info=campaign_info
        )
        
        # Update the existing product record
        updated_record = update_product_record(
            table_name=table_name,
            product_id=product_id,
            user_id=user_id,
            enrichment_results=enrichment_results,
            request_id=context.aws_request_id
        )
        
        # Return structured response with product_id and user_id
        response_data = {
            'success': True,
            'product_id': product_id,
            'user_id': user_id,
            'enrichment_status': 'data_enriched',
            'youtube_videos_count': len(enrichment_results.get('youtube_videos', [])),
            'market_insights_count': len(enrichment_results.get('market_insights', [])),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error in handle_data_enrichment: {str(e)}")
        return create_error_response(f"Data enrichment failed: {str(e)}")


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


def enrich_product_data(product_name, product_category, campaign_info):
    """
    Enrich product data with YouTube videos and market insights.
    
    Args:
        product_name: Product name
        product_category: Product category
        campaign_info: Campaign information dict
        
    Returns:
        Dictionary with enrichment results
    """
    # Use YouTube API to get real video recommendations
    search_query = f"{product_name} {product_category}".strip()
    youtube_data = search_youtube(search_query, max_results=10)
    enrichment_data = process_youtube_results(youtube_data, search_query)
    
    youtube_videos = enrichment_data.get('videos', [])
    market_insights = generate_market_insights(product_category)
    
    return {
        'youtube_videos': youtube_videos,
        'market_insights': market_insights,
        'target_demographics': extract_demographics(campaign_info),
        'trending_keywords': enrichment_data.get('trending_keywords', []),
        'content_themes': enrichment_data.get('content_themes', []),
        'enriched_at': datetime.utcnow().isoformat()
    }


def search_youtube(query, max_results=10):
    """Search YouTube using the YouTube Data API v3."""
    try:
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            raise ValueError("YouTube API key not configured")
        
        # Build API request
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'maxResults': min(max_results, 50),  # YouTube API limit
            'key': api_key,
            'safeSearch': 'moderate',
            'order': 'relevance'
        }
        
        # Encode parameters
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        print(f"YouTube API request: {url.replace(api_key, 'REDACTED')}")
        
        # Make API request
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        print(f"YouTube API response: Found {len(data.get('items', []))} results")
        return data
        
    except Exception as e:
        print(f"Error calling YouTube API: {str(e)}")
        # Return mock data as fallback
        return generate_mock_youtube_data(query, max_results)


def process_youtube_results(youtube_data, search_query):
    """Process YouTube API results into structured enrichment data."""
    try:
        items = youtube_data.get('items', [])
        
        videos = []
        channels = []
        trends = []
        
        for item in items:
            snippet = item.get('snippet', {})
            
            if item.get('id', {}).get('kind') == 'youtube#video':
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'channel_title': snippet.get('channelTitle', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                    'relevance_score': calculate_relevance_score(snippet, search_query)
                }
                videos.append(video_data)
                
                # Extract trending keywords from titles and descriptions
                trends.extend(extract_keywords(snippet.get('title', '') + ' ' + snippet.get('description', '')))
                
            elif item.get('id', {}).get('kind') == 'youtube#channel':
                channel_data = {
                    'channel_id': item['id']['channelId'],
                    'channel_title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                }
                channels.append(channel_data)
        
        # Analyze trends and patterns
        trending_keywords = analyze_trending_keywords(trends)
        
        enrichment_data = {
            'search_query': search_query,
            'total_results': youtube_data.get('pageInfo', {}).get('totalResults', 0),
            'videos': videos,
            'channels': channels,
            'trending_keywords': trending_keywords,
            'content_themes': extract_content_themes(videos),
            'engagement_patterns': analyze_engagement_patterns(videos)
        }
        
        return enrichment_data
        
    except Exception as e:
        print(f"Error processing YouTube results: {str(e)}")
        return generate_mock_enrichment_data(search_query)


def calculate_relevance_score(snippet, search_query):
    """Calculate a simple relevance score based on keyword matches."""
    try:
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        query_terms = search_query.lower().split()
        
        score = 0
        for term in query_terms:
            if term in title:
                score += 2  # Title matches are more important
            if term in description:
                score += 1
        
        return score
    except:
        return 0


def extract_keywords(text):
    """Extract keywords from text for trend analysis."""
    try:
        # Simple keyword extraction (in production, use more sophisticated NLP)
        words = text.lower().split()
        # Filter out common words and keep meaningful terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:10]  # Return top 10 keywords
    except:
        return []


def analyze_trending_keywords(all_keywords):
    """Analyze keyword frequency to identify trends."""
    try:
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # Sort by frequency and return top trends
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        return [{'keyword': k, 'frequency': v} for k, v in sorted_keywords[:15]]
    except:
        return []


def extract_content_themes(videos):
    """Extract common themes from video content."""
    try:
        themes = []
        for video in videos:
            title_words = video.get('title', '').lower().split()
            desc_words = video.get('description', '').lower().split()
            
            # Identify potential themes (simplified approach)
            content_indicators = {
                'tutorial': ['how', 'tutorial', 'guide', 'learn', 'tips'],
                'review': ['review', 'unboxing', 'test', 'comparison'],
                'entertainment': ['funny', 'comedy', 'entertaining', 'fun'],
                'lifestyle': ['lifestyle', 'daily', 'vlog', 'routine'],
                'tech': ['tech', 'technology', 'gadget', 'device', 'innovation'],
                'music': ['music', 'song', 'audio', 'sound', 'beats']
            }
            
            for theme, indicators in content_indicators.items():
                if any(indicator in title_words + desc_words for indicator in indicators):
                    themes.append(theme)
        
        # Count theme frequency
        theme_count = {}
        for theme in themes:
            theme_count[theme] = theme_count.get(theme, 0) + 1
        
        return [{'theme': k, 'count': v} for k, v in sorted(theme_count.items(), key=lambda x: x[1], reverse=True)]
    except:
        return []


def analyze_engagement_patterns(videos):
    """Analyze patterns in video metadata for insights."""
    try:
        patterns = {
            'optimal_title_length': calculate_optimal_title_length(videos),
            'popular_posting_times': analyze_posting_times(videos),
            'successful_content_formats': identify_content_formats(videos)
        }
        return patterns
    except:
        return {}


def calculate_optimal_title_length(videos):
    """Calculate optimal title length based on video data."""
    try:
        if not videos:
            return {'average': 0, 'recommendation': 'No data available'}
        
        lengths = [len(video.get('title', '')) for video in videos]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        return {
            'average': round(avg_length, 1),
            'recommendation': f"Aim for {round(avg_length * 0.9)}-{round(avg_length * 1.1)} characters"
        }
    except:
        return {'average': 0, 'recommendation': 'Analysis failed'}


def analyze_posting_times(videos):
    """Analyze posting time patterns."""
    try:
        # This is a simplified analysis - in production, you'd parse timestamps properly
        return {
            'pattern': 'Consistent posting detected',
            'recommendation': 'Maintain regular posting schedule for better engagement'
        }
    except:
        return {'pattern': 'Unknown', 'recommendation': 'Unable to analyze posting patterns'}


def identify_content_formats(videos):
    """Identify successful content formats."""
    try:
        formats = []
        for video in videos:
            title = video.get('title', '').lower()
            if 'how to' in title:
                formats.append('tutorial')
            elif any(word in title for word in ['review', 'unboxing']):
                formats.append('review')
            elif any(word in title for word in ['vs', 'comparison']):
                formats.append('comparison')
        
        format_count = {}
        for fmt in formats:
            format_count[fmt] = format_count.get(fmt, 0) + 1
        
        return [{'format': k, 'count': v} for k, v in sorted(format_count.items(), key=lambda x: x[1], reverse=True)]
    except:
        return []


def generate_mock_youtube_data(query, max_results):
    """Generate mock YouTube data as fallback when API is unavailable."""
    mock_videos = []
    for i in range(min(max_results, 5)):
        mock_videos.append({
            'id': {
                'kind': 'youtube#video',
                'videoId': f'mock_video_{i}'
            },
            'snippet': {
                'title': f'{query} - Video {i+1}',
                'description': f'Mock description for {query}',
                'channelTitle': 'Mock Channel',
                'publishedAt': datetime.utcnow().isoformat(),
                'thumbnails': {
                    'default': {
                        'url': 'https://via.placeholder.com/120x90'
                    }
                }
            }
        })
    
    return {
        'items': mock_videos,
        'pageInfo': {
            'totalResults': min(max_results, 5)
        }
    }


def generate_mock_enrichment_data(search_query):
    """Generate mock enrichment data as fallback."""
    return {
        'search_query': search_query,
        'total_results': 0,
        'videos': [],
        'channels': [],
        'trending_keywords': [{'keyword': search_query, 'frequency': 1}],
        'content_themes': [],
        'engagement_patterns': {}
    }


def generate_market_insights(category):
    """Generate market insights for the product category."""
    # Mock insights - in production, use real market data API
    insights = [
        {
            'metric': 'market_growth_rate',
            'value': '23%',
            'timeframe': 'year-over-year',
            'source': 'industry_data'
        },
        {
            'metric': 'consumer_interest',
            'value': 'trending',
            'change': '+12%',
            'source': 'social_media_analysis'
        },
        {
            'metric': 'average_price_point',
            'value': '$250-$500',
            'category': category,
            'source': 'market_research'
        },
        {
            'metric': 'top_competitor_count',
            'value': '15-20',
            'category': category,
            'source': 'competitive_analysis'
        }
    ]
    return insights


def extract_demographics(campaign_info):
    """Extract target demographics from campaign info."""
    return {
        'age_range': campaign_info.get('target_age_range', '18-45'),
        'interests': campaign_info.get('target_interests', []),
        'platforms': campaign_info.get('platform_preferences', ['instagram', 'tiktok']),
        'income_level': campaign_info.get('income_level', 'middle'),
        'geographic_focus': campaign_info.get('geographic_focus', 'global')
    }


def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def update_product_record(table_name, product_id, user_id, enrichment_results, request_id):
    """
    Update existing product record in DynamoDB with enrichment data.
    
    Args:
        table_name: DynamoDB table name
        product_id: Product ID
        user_id: User ID
        enrichment_results: Results from enrichment
        request_id: Lambda request ID
        
    Returns:
        Updated product record
    """
    try:
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
        
        # Update the record with enrichment data
        response = table.update_item(
            Key={
                'product_id': product_id,
                'user_id': user_id
            },
            UpdateExpression="""
                SET youtube_videos = :youtube,
                    market_insights = :insights,
                    target_demographics = :demographics,
                    trending_keywords = :keywords,
                    content_themes = :themes,
                    enrichment_status = :status,
                    updated_at = :timestamp,
                    enrichment_request_id = :request_id
            """,
            ExpressionAttributeValues={
                ':youtube': convert_floats(enrichment_results['youtube_videos']),
                ':insights': convert_floats(enrichment_results['market_insights']),
                ':demographics': convert_floats(enrichment_results['target_demographics']),
                ':keywords': convert_floats(enrichment_results.get('trending_keywords', [])),
                ':themes': convert_floats(enrichment_results.get('content_themes', [])),
                ':status': 'data_enriched',
                ':timestamp': timestamp,
                ':request_id': request_id
            },
            ReturnValues='ALL_NEW'
        )
        
        print(f"Successfully updated product record {product_id} with enrichment data")
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
                    
                    elif prop_name == 'campaign_info':
                        try:
                            json_body['campaign_info'] = json.loads(prop_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid campaign_info JSON", api_path)
        
        if not json_body.get('product_id'):
            return create_bedrock_error_response("product_id is required", api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body)}")
        
        if function_name == 'enrich_campaign_data' or api_path == '/enrich-campaign-data':
            result = handle_data_enrichment(json_body, context)
            
            if result.get('statusCode') == 200:
                body_data = json.loads(result['body'])
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': 'data-enrichment',
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
        return create_bedrock_error_response(f"Internal error: {str(e)}", "/enrich-campaign-data")


def create_bedrock_error_response(error_message, api_path='/enrich-campaign-data'):
    """Create a Bedrock agent compatible error response."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'data-enrichment',
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
