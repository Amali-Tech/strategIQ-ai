import json
import os
import urllib.request
import urllib.parse
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import uuid

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for data enrichment using YouTube API.
    Processes search queries and retrieves YouTube video data for campaign insights.
    
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
        
        if action_group != 'data-enrichment':
            return create_error_response(f"Invalid action group: {action_group}")
        
        if function_name == 'enrich_campaign_data':
            return handle_data_enrichment(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_bedrock_error_response(f"Internal error: {str(e)}")

def handle_data_enrichment(parameters, context):
    """Handle data enrichment with YouTube API integration."""
    try:
        # Extract parameters
        product_id = parameters.get('product_id', '')
        user_id = parameters.get('user_id', '')
        search_query = parameters.get('search_query', '')
        max_results = parameters.get('max_results', 10)
        content_type = parameters.get('content_type', 'all')  # 'all', 'videos', 'channels', 'playlists'
        
        # Validate required parameters
        if not product_id:
            return create_error_response("product_id parameter is required")
        if not user_id:
            return create_error_response("user_id parameter is required")
        
        # Convert max_results to int if it's a string
        try:
            max_results = int(max_results)
        except (ValueError, TypeError):
            max_results = 10
        
        print(f"Processing search query: {search_query} for product_id: {product_id}, user_id: {user_id}")
        print(f"Content type: {content_type}, Max results: {max_results}")
        
        if not search_query:
            return create_error_response("search_query parameter is required")
        
        # Call YouTube API
        youtube_results = search_youtube(search_query, max_results, content_type)
        
        # Process and structure the results
        enrichment_data = process_youtube_results(youtube_results, search_query)
        
        # Store enrichment data in DynamoDB products table
        enrichment_id = store_enrichment_data_to_products(product_id, user_id, enrichment_data, search_query, context)
        
        # Prepare response
        response_data = {
            'success': True,
            'enrichment_id': enrichment_id,
            'product_id': product_id,
            'user_id': user_id,
            'search_query': search_query,
            'results_count': len(enrichment_data.get('videos', [])),
            'enrichment_data': enrichment_data,
            'insights': generate_content_insights(enrichment_data),
            'timestamp': context.aws_request_id
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error in handle_data_enrichment: {str(e)}")
        return create_error_response(f"Data enrichment failed: {str(e)}")

def search_youtube(query, max_results=10, content_type='all'):
    """Search YouTube using the Data API v3."""
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
        
        # Filter by content type if specified
        if content_type == 'videos':
            params['type'] = 'video'
        elif content_type == 'channels':
            params['type'] = 'channel'
        elif content_type == 'playlists':
            params['type'] = 'playlist'
        
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
        raise

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
        raise

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

def generate_content_insights(enrichment_data):
    """Generate actionable insights from the enrichment data."""
    try:
        insights = {
            'content_opportunities': [],
            'trending_topics': [],
            'audience_preferences': [],
            'competitive_landscape': []
        }
        
        # Content opportunities based on trending keywords
        trending_keywords = enrichment_data.get('trending_keywords', [])[:5]
        for keyword_data in trending_keywords:
            insights['content_opportunities'].append({
                'opportunity': f"Create content around '{keyword_data['keyword']}'",
                'relevance': keyword_data['frequency'],
                'reasoning': f"High frequency ({keyword_data['frequency']}) indicates strong audience interest"
            })
        
        # Trending topics from content themes
        content_themes = enrichment_data.get('content_themes', [])[:3]
        for theme_data in content_themes:
            insights['trending_topics'].append({
                'topic': theme_data['theme'],
                'prevalence': theme_data['count'],
                'recommendation': f"Consider incorporating {theme_data['theme']} elements in your campaign"
            })
        
        # Audience preferences from engagement patterns
        patterns = enrichment_data.get('engagement_patterns', {})
        if patterns:
            insights['audience_preferences'].append({
                'preference': 'Title optimization',
                'detail': patterns.get('optimal_title_length', {}).get('recommendation', 'Optimize title length'),
                'impact': 'High'
            })
        
        # Competitive landscape from channel analysis
        channels = enrichment_data.get('channels', [])
        if channels:
            insights['competitive_landscape'].append({
                'insight': f"Found {len(channels)} relevant channels in this space",
                'recommendation': "Analyze top channels for content strategy ideas",
                'channels': [ch.get('channel_title', '') for ch in channels[:3]]
            })
        
        return insights
        
    except Exception as e:
        print(f"Error generating insights: {str(e)}")
        return {'error': 'Could not generate insights'}

def store_enrichment_data(enrichment_data, search_query, context=None):
    """Store enrichment data in DynamoDB."""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME')
        if not table_name:
            print("Warning: DynamoDB table name not configured")
            return "no-storage"
        
        table = dynamodb.Table(table_name)
        
        # Convert float values to Decimal for DynamoDB compatibility
        def convert_floats(obj):
            if isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(v) for v in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            else:
                return obj
        
        enrichment_record = {
            'enrichment_id': f"enrich_{hash(search_query)}_{len(enrichment_data.get('videos', []))}",
            'search_query': search_query,
            'enrichment_data': convert_floats(enrichment_data),
            'created_at': context.aws_request_id if context else 'unknown',
            'ttl': int(context.get_remaining_time_in_millis() / 1000) + 86400 if context else 86400  # 24 hours TTL
        }
        
        # Store in DynamoDB
        table.put_item(Item=enrichment_record)
        
        print(f"Successfully saved enrichment record {enrichment_record['enrichment_id']} to DynamoDB")
        return enrichment_record['enrichment_id']
        
    except Exception as e:
        print(f"Error storing enrichment data: {str(e)}")
        return "storage-failed"

def store_enrichment_data_to_products(product_id, user_id, enrichment_data, search_query, context=None):
    """Save or update data enrichment in the products table."""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME')
        if not table_name:
            print("Warning: DynamoDB table name not configured")
            return f"enrich_{hash(search_query)}_{len(enrichment_data.get('videos', []))}"
        
        table = dynamodb.Table(table_name)
        
        # Convert float values to Decimal for DynamoDB compatibility
        def convert_floats(obj):
            if isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(v) for v in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            else:
                return obj
        
        enrichment_record = {
            'enrichment_id': f"enrich_{hash(search_query)}_{len(enrichment_data.get('videos', []))}",
            'search_query': search_query,
            'enrichment_data': convert_floats(enrichment_data),
            'insights': convert_floats(generate_content_insights(enrichment_data)),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
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
            # Update existing record with data enrichment
            update_expression = "SET data_enrichment = :enrichment, updated_at = :updated_at"
            expression_values = {
                ':enrichment': enrichment_record,
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            table.update_item(
                Key={'product_id': product_id, 'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            print(f"Updated data enrichment for product {product_id}")
        else:
            # Create new product record with data enrichment
            new_record = {
                'product_id': product_id,
                'user_id': user_id,
                'data_enrichment': enrichment_record,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=new_record)
            print(f"Created new product record {product_id} with data enrichment")
        
        return enrichment_record['enrichment_id']
        
    except Exception as e:
        print(f"Error storing enrichment data to products table: {str(e)}")
        return f"enrich_{hash(search_query)}_{len(enrichment_data.get('videos', []))}"

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        # Extract parameters from Bedrock agent format
        request_body = event.get('requestBody', {})
        function_name = event.get('function', '')
        api_path = event.get('apiPath', '')
        
        print(f"Function: {function_name}, API Path: {api_path}")
        
        # Extract JSON body from Bedrock request
        json_body = extract_json_from_bedrock_request(request_body, api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body, default=str)}")
        
        if function_name == 'enrich_campaign_data' or api_path in ['/enrich-data', '/enrich-campaign-data']:
            # Validate required fields
            search_query = json_body.get('search_query')
            product_id = json_body.get('product_id')
            user_id = json_body.get('user_id')
            
            if not search_query:
                return create_bedrock_error_response("search_query is required", api_path)
            if not product_id:
                return create_bedrock_error_response("product_id is required", api_path)
            if not user_id:
                return create_bedrock_error_response("user_id is required", api_path)
            
            # Call the enrichment function with the extracted parameters
            result = handle_data_enrichment(json_body, context)
            
            # Convert response to Bedrock format
            if result.get('statusCode') == 200:
                body_data = json.loads(result['body'])
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': 'data-enrichment',
                        'apiPath': api_path,  # Use the same path that was called
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
            return create_bedrock_error_response(f"Unknown function: {function_name}, path: {api_path}", api_path)
            
    except Exception as e:
        print(f"Error in handle_bedrock_agent_invocation: {str(e)}")
        return create_bedrock_error_response(f"Processing error: {str(e)}")

def extract_json_from_bedrock_request(request_body, api_path):
    """Extract and construct JSON from Bedrock request body."""
    try:
        content = request_body.get('content', {})
        json_body = {}
        
        # Handle application/json content type with properties array
        if 'application/json' in content and 'properties' in content['application/json']:
            properties = content['application/json']['properties']
            for prop in properties:
                prop_name = prop.get('name', '')
                prop_value = prop.get('value', '')
                
                # Handle different value types
                if prop_name == 'product_id':
                    json_body['product_id'] = prop_value
                elif prop_name == 'user_id':
                    json_body['user_id'] = prop_value if prop_value else 'anonymous'
                elif prop_name == 'search_query':
                    json_body['search_query'] = prop_value
                elif prop_name == 'max_results':
                    try:
                        json_body['max_results'] = int(prop_value) if prop_value else 10
                    except:
                        json_body['max_results'] = 10
                elif prop_name == 'content_type':
                    json_body['content_type'] = prop_value if prop_value else 'all'
                else:
                    json_body[prop_name] = prop_value
        
        return json_body
        
    except Exception as e:
        print(f"Error extracting JSON from Bedrock request: {str(e)}")
        raise

def create_error_response(error_message):
    """Create an error response for direct invocation."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }

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