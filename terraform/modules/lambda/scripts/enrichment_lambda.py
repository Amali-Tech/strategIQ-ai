import json
import base64
import hashlib
import os
import boto3
from decimal import Decimal
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from botocore.exceptions import ClientError

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

# Set environment variables
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
DYNAMODB_TABLE = os.environ.get('ENRICHED_TABLE_NAME', 'EnrichedDataTable')  # Table 2 for enriched data with default value
CAMPAIGN_SQS_QUEUE_URL = os.environ.get('CAMPAIGN_SQS_QUEUE_URL')  # SQS queue for campaign generation

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Only initialize the table if we have a valid table name
if not DYNAMODB_TABLE:
    print("WARNING: ENRICHED_TABLE_NAME environment variable not set. Using default table name.")
    
# Create table reference - we'll check if it exists when we try to use it
table = dynamodb.Table(DYNAMODB_TABLE)

# Check if SQS queue URL is set
if not CAMPAIGN_SQS_QUEUE_URL:
    print("WARNING: CAMPAIGN_SQS_QUEUE_URL environment variable not set. Pipeline will store in DynamoDB but not trigger campaign generation.")

def get_youtube_service():
    """Initialize YouTube API service"""
    if not YOUTUBE_API_KEY:
        print("WARNING: YouTube API key not set. YouTube service will not be available.")
        return None
        
    try:            
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
    except Exception as e:
        print(f"Error initializing YouTube service: {e}")
        return None

def search_youtube_videos(query, max_results=5):
    """
    Search YouTube for relevant videos based on the query
    Returns a list of video data including title, description, thumbnail URL, video ID
    """
    youtube = get_youtube_service()
    if not youtube:
        return []
    
    try:
        # Search for videos related to the query
        search_request = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=max_results,
            type="video",
            relevanceLanguage="en",
            order="relevance"  # Other options: date, rating, viewCount
        )
        search_response = search_request.execute()
        
        # Extract video IDs to get more details
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        
        if not video_ids:
            return []
            
        # Get detailed information about the videos
        videos_request = youtube.videos().list(
            id=','.join(video_ids),
            part="snippet,statistics,contentDetails"
        )
        videos_response = videos_request.execute()
        
        # Process and return the results
        results = []
        for item in videos_response.get('items', []):
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            
            video_data = {
                'videoId': item['id'],
                'title': snippet['title'],
                'description': snippet.get('description', '')[:500],  # Limit description length
                'publishedAt': snippet['publishedAt'],
                'channelTitle': snippet['channelTitle'],
                'thumbnailUrl': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'viewCount': Decimal(str(statistics.get('viewCount', 0))),
                'likeCount': Decimal(str(statistics.get('likeCount', 0))),
                'commentCount': Decimal(str(statistics.get('commentCount', 0))),
                'url': f"https://www.youtube.com/watch?v={item['id']}"
            }
            results.append(video_data)
        
        return results
        
    except HttpError as e:
        print(f"YouTube API error: {e}")
        return []
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

def build_search_query(product_attributes, product_categories):
    """
    Build an optimized search query for YouTube based on product attributes and categories
    """
    query_parts = []
    
    # Extract product attributes (from Rekognition)
    if product_attributes:
        # Sort by confidence and get top attributes
        sorted_attributes = sorted(
            [
                {
                    'name': attr.get('M', {}).get('attribute', {}).get('S', ''),
                    'confidence': Decimal(str(attr.get('M', {}).get('confidence', {}).get('N', '0')))
                }
                for attr in product_attributes
            ],
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )[:3]
        
        # Add top attributes to query
        for attr in sorted_attributes:
            if attr['name']:
                query_parts.append(attr['name'])
    
    # Add product categories
    if product_categories:
        for category in product_categories[:2]:  # Limit to top 2 categories
            category_name = category.get('S', '')
            if category_name:
                query_parts.append(category_name)
    
    # Add marketing-related keywords based on product type
    is_footwear = any(attr.get('M', {}).get('attribute', {}).get('S', '').lower() in ['footwear', 'shoe', 'boot', 'sneaker'] 
                      for attr in product_attributes)
    is_clothing = any(attr.get('M', {}).get('attribute', {}).get('S', '').lower() in ['clothing', 'apparel', 'fashion'] 
                      for attr in product_attributes)
    
    marketing_terms = []
    
    if is_footwear:
        marketing_terms.extend(['footwear trends', 'shoe marketing'])
    elif is_clothing:
        marketing_terms.extend(['fashion marketing', 'clothing trends'])
    else:
        marketing_terms.append('product marketing')
        
    # Add general marketing terms
    marketing_terms.append('campaign ideas')
    
    # Build the final query
    base_query = ' '.join(part for part in query_parts if part)[:100]  # Limit length
    marketing_query = ' '.join(marketing_terms)
    
    final_query = f"{base_query} {marketing_query}"
    print(f"Built YouTube search query: {final_query}")
    
    return final_query

def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values in a dictionary or list to Decimal
    This is required for DynamoDB which doesn't support float types
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    return obj

def send_to_sqs(message_data):
    """
    Send a message to SQS to trigger the campaign generator
    Returns (success, error_message) tuple
    """
    if not CAMPAIGN_SQS_QUEUE_URL:
        return False, "SQS queue URL not set"
    
    try:
        # Convert any Decimal objects to float for JSON serialization
        message_json = json.dumps(message_data, cls=DecimalEncoder)
        
        # Send the message to SQS
        response = sqs.send_message(
            QueueUrl=CAMPAIGN_SQS_QUEUE_URL,
            MessageBody=message_json
        )
        
        message_id = response.get('MessageId')
        if message_id:
            print(f"Successfully sent message to SQS with MessageId: {message_id}")
            return True, None
        else:
            return False, "No MessageId returned from SQS"
            
    except ClientError as e:
        error_message = f"Error sending to SQS: {str(e)}"
        print(error_message)
        return False, error_message
    except Exception as e:
        error_message = f"Unexpected error sending to SQS: {str(e)}"
        print(error_message)
        return False, error_message

def validate_environment():
    """Validate that all required environment variables are set"""
    missing_vars = []
    
    if not YOUTUBE_API_KEY:
        missing_vars.append("YOUTUBE_API_KEY")
    
    if not DYNAMODB_TABLE:
        missing_vars.append("ENRICHED_TABLE_NAME")
    
    if not CAMPAIGN_SQS_QUEUE_URL:
        missing_vars.append("CAMPAIGN_SQS_QUEUE_URL")
    
    return missing_vars

def lambda_handler(event, context):
    """
    EventBridge Pipe Enrichment Lambda Handler
    
    This function:
    1. Receives a DynamoDB stream record via EventBridge Pipe
    2. Extracts product data and image analysis from the stream
    3. Searches YouTube for related videos
    4. Stores the enriched data in Table 2 with a status field for frontend tracking
    5. Returns the enriched event to be passed to the target Lambda
    """
    try:
        # Validate environment variables
        missing_vars = validate_environment()
        if missing_vars:
            print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
            return {
                "error": f"Configuration error: Missing {', '.join(missing_vars)}",
                "pipeline_status": "failed"
            }
        
        # Validate DynamoDB table exists
        try:
            table.load()
        except Exception as e:
            print(f"ERROR: DynamoDB table {DYNAMODB_TABLE} not found or inaccessible: {e}")
            return {
                "error": f"DynamoDB table {DYNAMODB_TABLE} not found or inaccessible",
                "pipeline_status": "failed"
            }
        
        print("Received event:", json.dumps(event, cls=DecimalEncoder))
        
        # Log the event structure for debugging
        if 'Records' in event:
            print(f"Event contains 'Records' array with {len(event['Records'])} items")
            if len(event['Records']) > 0:
                print(f"First record eventName: {event['Records'][0].get('eventName')}")
                print(f"DynamoDB data keys: {list(event['Records'][0]['dynamodb'].keys() if 'dynamodb' in event['Records'][0] else [])}")
        
        # For EventBridge Pipe, we need to extract the DynamoDB record
        # The structure depends on how the Pipe is configured
        if 'Records' in event and len(event['Records']) > 0:
            # Standard DynamoDB Stream format - Lambda test console and standard DynamoDB streams
            record = event['Records'][0]['dynamodb']
        elif 'detail' in event:
            # EventBridge Rule format
            dynamodb_event = event['detail']
            if 'dynamodb' in dynamodb_event:
                record = dynamodb_event['dynamodb']
            else:
                print("Unexpected event format: No dynamodb data in detail")
                return {"error": "Invalid event format", "pipeline_status": "failed"}
        elif 'records' in event and len(event['records']) > 0:
            # Direct pipe format with potentially multiple records - lowercase 'records'
            # For simplicity, we'll process just the first record
            record = event['records'][0]['dynamodb']
        elif 'dynamodb' in event:
            # Direct DynamoDB stream format
            record = event['dynamodb']
        else:
            print("Unexpected event format")
            return {"error": "Invalid event format", "pipeline_status": "failed"}
            
        # Extract data from the DynamoDB record (NewImage from the stream)
        if 'NewImage' in record:
            new_image = record['NewImage']
            
            # Extract important information from Table 1 record based on the provided structure
            record_id = new_image.get('id', {}).get('S', '')
            public_url = new_image.get('public_url', {}).get('S', '')
            s3_url = new_image.get('s3_url', {}).get('S', '')
            bucket_name = new_image.get('bucket_name', {}).get('S', '')
            object_key = new_image.get('object_key', {}).get('S', '')
            image_hash = new_image.get('imageHash', {}).get('S', '')
            created_at = new_image.get('created_at', {}).get('S', '')
            
            # Get product attributes and categories
            product_attributes = new_image.get('product_attributes', {}).get('L', [])
            product_categories = new_image.get('product_categories', {}).get('L', [])
            
            # Get raw analysis for additional information
            raw_analysis_str = new_image.get('raw_analysis', {}).get('S', '{}')
            
            try:
                raw_analysis = json.loads(raw_analysis_str)
            except json.JSONDecodeError:
                raw_analysis = {}
            
            # Generate a unique image hash if not provided
            # This will be used as the partition key for Table 2
            # image_hash = base64.b64encode(hashlib.sha256(object_key.encode()).digest()).decode('utf-8')
                
            # Build search query based on product attributes and categories
            search_query = build_search_query(product_attributes, product_categories)
            
            # Search for relevant YouTube videos
            try:
                youtube_results = search_youtube_videos(search_query, max_results=5)
                if not youtube_results and YOUTUBE_API_KEY:
                    print("WARNING: YouTube search returned no results")
            except Exception as e:
                print(f"ERROR during YouTube search: {e}")
                youtube_results = []
                print("Continuing with empty YouTube results")
            
            # Extract all product labels for better context in the next stage
            product_labels = []
            for attr in product_attributes:
                attribute_name = attr.get('M', {}).get('attribute', {}).get('S', '')
                confidence = attr.get('M', {}).get('confidence', {}).get('N', '0')
                if attribute_name:
                    product_labels.append({
                        'name': attribute_name,
                        'confidence': Decimal(str(confidence))
                    })
            
            # Timestamp for tracking
            current_timestamp = new_image.get('analysis_timestamp', {}).get('S', '') or created_at
            
            # Prepare data for Table 2 with a status field for frontend tracking
            enriched_data = {
                'imageHash': image_hash,  # Partition key
                'recordId': record_id,
                'originalData': {
                    'public_url': public_url,
                    's3_url': s3_url,
                    'bucket_name': bucket_name,
                    'object_key': object_key,
                    'product_labels': product_labels,
                    'product_categories': [cat.get('S', '') for cat in product_categories],
                    'raw_analysis': raw_analysis
                },
                'youtubeResults': youtube_results,
                'created_at': created_at,
                'enriched_at': datetime.now().isoformat(),
                'pipeline_status': 'enriched',  # Status for frontend tracking
                'next_step': 'content_generation'  # Next step in the pipeline
            }
            
            # Store enriched data in Table 2
            try:
                # Check again if table is accessible before putting item
                if not DYNAMODB_TABLE:
                    raise ValueError("ENRICHED_TABLE_NAME environment variable is not set")
                
                # Convert any float values to Decimal for DynamoDB compatibility
                enriched_data = convert_floats_to_decimal(enriched_data)
                    
                table.put_item(Item=enriched_data)
                print(f"Successfully stored enriched data for imageHash: {image_hash}")
            except Exception as e:
                print(f"Error storing enriched data: {e}")
                
                # Continue even if we can't store to DynamoDB - just log the error
                # This allows the pipeline to continue to the next step
                print("WARNING: Continuing pipeline despite DynamoDB write failure")
                
                # Still include the enriched data in the return value but mark as partial success
                sqs_message = {
                    "warning": f"Failed to store enriched data: {str(e)}",
                    "imageHash": image_hash,
                    "recordId": record_id, 
                    "youtubeResults": youtube_results,
                    "object_key": object_key,
                    "pipeline_status": "enriched_partial",  # Indicate partial success
                    "next_step": "content_generation"
                }
            else:
                # Create the message for SQS with the enriched data
                sqs_message = {
                    'imageHash': image_hash,
                    'recordId': record_id,
                    'youtubeResults': youtube_results,
                    'object_key': object_key,
                    'pipeline_status': 'enriched',  # Status for frontend tracking
                    'next_step': 'content_generation'
                }
            
            # Send the enriched data to SQS for campaign generation
            if CAMPAIGN_SQS_QUEUE_URL:
                success, error = send_to_sqs(sqs_message)
                
                if success:
                    print(f"Successfully sent message to SQS for campaign generation")
                    sqs_message["sqs_status"] = "sent"
                else:
                    print(f"Failed to send message to SQS: {error}")
                    sqs_message["sqs_status"] = "failed"
                    sqs_message["sqs_error"] = error
            else:
                print("Skipping SQS message (CAMPAIGN_SQS_QUEUE_URL not set)")
                sqs_message["sqs_status"] = "skipped"
            
            # Return enriched event as Lambda response
            return sqs_message
            
        else:
            print("No NewImage found in the DynamoDB record")
            return {"error": "No new data found", "pipeline_status": "failed"}
            
    except Exception as e:
        print(f"Error processing event: {e}")
        return {"error": str(e), "pipeline_status": "failed"}
