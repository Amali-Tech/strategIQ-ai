import json
import os
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

# Set up environment variables with defaults
ANALYSIS_TABLE = os.environ.get('ANALYSIS_TABLE', 'product-analysis-table')
ENRICHED_TABLE = os.environ.get('ENRICHED_TABLE', 'enriched-products-table')

# Initialize DynamoDB resources
dynamodb = boto3.resource('dynamodb')
analysis_table = dynamodb.Table(ANALYSIS_TABLE)
enriched_table = dynamodb.Table(ENRICHED_TABLE)

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def extract_from_dynamodb_format(obj):
    """
    Recursively extract values from DynamoDB attribute format.
    Converts from {'S': 'value'} to 'value', {'N': '123'} to 123, etc.
    """
    if not isinstance(obj, dict):
        return obj
    
    # Check for DynamoDB attribute format
    if len(obj) == 1:
        attr_type = next(iter(obj))
        if attr_type in ('S', 'N', 'BOOL', 'B'):
            value = obj[attr_type]
            if attr_type == 'N':
                try:
                    return Decimal(value)
                except:
                    return value
            return value
        elif attr_type == 'M':
            return {k: extract_from_dynamodb_format(v) for k, v in obj[attr_type].items()}
        elif attr_type == 'L':
            return [extract_from_dynamodb_format(item) for item in obj[attr_type]]
    
    # Regular dictionary
    return {k: extract_from_dynamodb_format(v) for k, v in obj.items()}

def get_item_by_hash(image_hash, table_name=None):
    """
    Fetch an item from DynamoDB using the image hash as key
    
    Args:
        image_hash: The image hash to look up
        table_name: Optional specific table to check (can be 'analysis' or 'enriched')
                   If None, will check enriched first, then analysis
    """
    try:
        print(f"Fetching record with imageHash: {image_hash}")
        
        if not isinstance(image_hash, str):
            print(f"Converting imageHash from {type(image_hash)} to string")
            image_hash = str(image_hash)
        
        # Define which tables to check and in what order
        tables_to_check = []
        
        if table_name == 'analysis':
            tables_to_check = [(analysis_table, 'analysis')]
        elif table_name == 'enriched':
            tables_to_check = [(enriched_table, 'enriched')]
        else:
            # Default: check enriched first, then analysis
            tables_to_check = [(enriched_table, 'enriched'), (analysis_table, 'analysis')]
        
        # Try each table in order
        for table, table_name in tables_to_check:
            try:
                print(f"Checking {table_name} table...")
                
                # Use different key name based on table:
                # - 'imageHash' for enriched table
                # - 'id' for analysis table
                key_name = 'imageHash' if table_name == 'enriched' else 'id'
                
                # Ensure the key is properly formatted before using it
                try:
                    # Some imageHash values contain base64 characters (+ / =) that might have been URL-encoded
                    # Make sure we're using the clean version for the database lookup
                    lookup_key = image_hash.strip()
                    response = table.get_item(Key={key_name: lookup_key})
                    item = response.get('Item', {})
                except Exception as key_error:
                    print(f"Error using key {lookup_key}: {key_error}. Trying fallback...")
                    # If that fails, try with the original key as a fallback
                    response = table.get_item(Key={key_name: image_hash})
                    item = response.get('Item', {})
                
                if item:
                    print(f"Found record in {table_name} table")
                    # Extract from DynamoDB format if needed and convert Decimals
                    item = extract_from_dynamodb_format(item)
                    
                    # Add which table it came from
                    item['source_table'] = table_name
                    return item
            except ClientError as e:
                print(f"Error checking {table_name} table: {e}")
                continue
        
        # If we get here, the item wasn't found in any table
        print(f"No record found for hash: {image_hash} in any table")
        return None
        
    except Exception as e:
        print(f"Error fetching record from DynamoDB: {e}")
        return None

def get_status_only(image_hash, table_name=None):
    """
    Get only the pipeline status and next step information from the DynamoDB record
    
    Args:
        image_hash: The image hash to look up
        table_name: Optional specific table to check ('analysis' or 'enriched')
                   If None, will check both tables (enriched first, then analysis)
    """
    # Check if this exists in the specified table or both tables
    item = get_item_by_hash(image_hash, table_name=table_name)
    
    if not item:
        print(f"No item found for status check with hash: {image_hash}, table: {table_name}")
        return None
    
    # Simplified response with just pipeline status and next step
    status_info = {
        "imageHash": image_hash,
        "lookup_table": table_name or "both"
    }
    
    # Determine pipeline status and next step based on the table
    if item.get("source_table") == "enriched":
        # For enriched table, use the actual pipeline_status field
        status_info["pipeline_status"] = item.get("pipeline_status", "unknown")
        
        # Add next step if available
        if "next_step" in item:
            status_info["next_step"] = item.get("next_step")
        else:
            # Default next step based on pipeline status
            if item.get("pipeline_status") == "completed":
                status_info["next_step"] = "done"
            elif item.get("generated_at"):
                status_info["next_step"] = "done"
            else:
                status_info["next_step"] = "content_generation"
    else:
        # For analysis table - set status based on presence of analysis
        if item.get("analysis_timestamp"):
            status_info["pipeline_status"] = "analyzed"
            status_info["next_step"] = "enrichment"
        else:
            status_info["pipeline_status"] = "processing"
            status_info["next_step"] = "analysis"
    
    return status_info

def build_response(status_code, body):
    """
    Build a standardized API Gateway response
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # For CORS support
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    """
    Main Lambda handler for API Gateway requests
    
    Supports multiple path patterns:
    1. /status/{imageHash} - Returns status info checking both tables (enriched first, then analysis)
    2. /product/{imageHash} - Returns the full product information from both tables (enriched preferred)
    3. /analysis/{imageHash} - Returns information specifically from the analysis table
    4. /enriched/{imageHash} - Returns information specifically from the enriched table
    5. /pipeline/{imageHash} - Returns complete pipeline status combining data from both tables
    
    Also handles direct queries with imageHash parameter
    """
    request_id = context.aws_request_id if context else 'local'
    print(f"Request ID {request_id} - Received event: {json.dumps(event)}")
    
    # Start timing the request for performance logging
    import time
    start_time = time.time()
    
    try:
        # Extract the image hash from different possible sources
        image_hash = None
        
        # Check path parameters
        if 'pathParameters' in event and event['pathParameters']:
            image_hash = event['pathParameters'].get('imageHash')
        
        # Check query string parameters if not found in path
        if not image_hash and 'queryStringParameters' in event and event['queryStringParameters']:
            image_hash = event['queryStringParameters'].get('imageHash')
        
        # Check direct parameter
        if not image_hash:
            image_hash = event.get('imageHash')
        
        if not image_hash:
            return build_response(400, {"error": "Missing imageHash parameter"})
            
        # URL-decode the imageHash to handle special characters
        try:
            import urllib.parse
            # URL-decode the image hash to handle '+', '/', '=' and other special characters
            image_hash = urllib.parse.unquote(image_hash)
            print(f"URL-decoded imageHash: {image_hash}")
        except Exception as decode_error:
            print(f"Warning: Error decoding imageHash: {decode_error}. Using as-is.")
        
        # Determine the request type based on the path
        path = event.get('path', '').lower()
        resource = event.get('resource', '').lower()
        
        # Handle different endpoint types
        if '/status/' in path or resource == '/status/{imagehash}':
            # Status request - return minimal information (checking both tables)
            status_info = get_status_only(image_hash)
            if status_info:
                return build_response(200, status_info)
            else:
                return build_response(404, {"error": "Product not found"})
                
        elif '/analysis/' in path or resource == '/analysis/{imagehash}':
            # Analysis table specific request
            item = get_item_by_hash(image_hash, table_name='analysis')
            if item:
                return build_response(200, item)
            else:
                return build_response(404, {"error": "Product not found in analysis table"})
                
        elif '/enriched/' in path or resource == '/enriched/{imagehash}':
            # Enriched table specific request
            item = get_item_by_hash(image_hash, table_name='enriched')
            if item:
                return build_response(200, item)
            else:
                return build_response(404, {"error": "Product not found in enriched table"})
                
        elif '/pipeline/' in path or resource == '/pipeline/{imagehash}':
            # Complete pipeline status - combine data from both tables
            enriched_item = get_item_by_hash(image_hash, table_name='enriched')
            analysis_item = get_item_by_hash(image_hash, table_name='analysis')
            
            if not enriched_item and not analysis_item:
                return build_response(404, {"error": "Product not found in any stage of pipeline"})
                
            # Build complete pipeline status
            pipeline_status = {
                "query_hash": image_hash,
                "analysis_complete": analysis_item is not None,
                "enrichment_complete": enriched_item is not None,
                "content_generation_complete": False,
                "pipeline_status": "unknown"
            }
            
            # Add data from analysis table if available
            if analysis_item:
                pipeline_status.update({
                    "id": analysis_item.get("id"),
                    "analysis_timestamp": analysis_item.get("analysis_timestamp"),
                    "bucket_name": analysis_item.get("bucket_name"),
                    "object_key": analysis_item.get("object_key"),
                    "public_url": analysis_item.get("public_url"),
                    "is_appropriate_content": analysis_item.get("is_appropriate_content", True)
                })
                
                # Add label and text counts
                if "labels_count" in analysis_item:
                    pipeline_status["labels_count"] = analysis_item.get("labels_count")
                elif "product_attributes" in analysis_item:
                    pipeline_status["labels_count"] = len(analysis_item.get("product_attributes", []))
                
                if "text_count" in analysis_item:
                    pipeline_status["text_count"] = analysis_item.get("text_count")
                    
            # Add data from enriched table if available
            if enriched_item:
                pipeline_status.update({
                    "imageHash": enriched_item.get("imageHash"),
                    "recordId": enriched_item.get("recordId"),
                    "enrichment_timestamp": enriched_item.get("enriched_at"),
                    "generation_timestamp": enriched_item.get("generated_at"),
                    "enrichment_status": enriched_item.get("pipeline_status", "unknown"),
                    "content_generation_complete": enriched_item.get("generated_at") is not None,
                    "next_step": enriched_item.get("next_step")
                })
                
                # Check for campaigns/content in the enriched table
                if "campaignsJSON" in enriched_item:
                    campaigns_json = enriched_item.get("campaignsJSON", {})
                    pipeline_status["has_campaigns"] = True
                    
                    # Check if it's the new structured format with output field
                    if "output" in campaigns_json:
                        pipeline_status["campaign_format"] = "structured"
                        # Try to extract details from the output structure
                        try:
                            if "message" in campaigns_json.get("output", {}):
                                if "content" in campaigns_json.get("output", {}).get("message", {}):
                                    # Successfully generated content
                                    pipeline_status["has_campaign_content"] = True
                                    pipeline_status["usage"] = campaigns_json.get("usage", {})
                        except Exception as e:
                            pipeline_status["campaign_extraction_error"] = str(e)
                    
                    # Check for traditional format
                    elif isinstance(campaigns_json, dict):
                        if "campaigns" in campaigns_json:
                            pipeline_status["campaignCount"] = len(campaigns_json.get("campaigns", []))
                        if "content_ideas" in campaigns_json:
                            pipeline_status["contentIdeasCount"] = len(campaigns_json.get("content_ideas", []))
            
            # Determine overall pipeline status
            if enriched_item and enriched_item.get("generated_at"):
                pipeline_status["pipeline_status"] = "completed"
            elif enriched_item:
                pipeline_status["pipeline_status"] = "enriched"
            elif analysis_item:
                pipeline_status["pipeline_status"] = "analyzed"
            
            return build_response(200, pipeline_status)
                
        else:
            # Default: full product request (from either table, prioritizing enriched)
            item = get_item_by_hash(image_hash)
            if not item:
                return build_response(404, {"error": "Product not found"})
                
            # Process enriched data with campaignsJSON to extract the content if possible
            if item.get("source_table") == "enriched" and "campaignsJSON" in item:
                try:
                    campaigns_json = item.get("campaignsJSON", {})
                    
                    # Check if it's the new structure with output field containing messages
                    if "output" in campaigns_json and "message" in campaigns_json.get("output", {}):
                        message = campaigns_json.get("output", {}).get("message", {})
                        
                        if "content" in message and isinstance(message.get("content"), list):
                            content_list = message.get("content", [])
                            
                            # Extract JSON from content if possible
                            for content_item in content_list:
                                if isinstance(content_item, dict) and "text" in content_item:
                                    text_content = content_item.get("text")
                                    
                                    try:
                                        # Try to parse the text as JSON
                                        parsed_json = json.loads(text_content)
                                        
                                        # Replace the raw campaignsJSON with the parsed content
                                        item["parsedCampaigns"] = parsed_json
                                        break
                                    except json.JSONDecodeError:
                                        # If not valid JSON, keep as is
                                        pass
                except Exception as e:
                    # If any error in parsing, add an error message but continue
                    item["campaignParsingError"] = str(e)
            
            # Log performance metrics
            end_time = time.time()
            processing_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            print(f"Request ID {request_id} - Processing completed in {processing_time}ms")
            
            # Add performance metrics to the response
            item["_processing_time_ms"] = processing_time
            return build_response(200, item)
                
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        
        # Log the full error details
        print(f"Request ID {request_id} - Error processing request: {str(e)}")
        print(f"Detailed error: {error_details}")
        
        # Calculate error processing time
        end_time = time.time()
        processing_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        # Return a more detailed error response with request context
        error_response = {
            "error": str(e),
            "message": "Internal server error",
            "request_id": request_id,
            "processing_time_ms": processing_time
        }
        
        # Include debug info in dev environments
        if os.environ.get('DEBUG', 'false').lower() == 'true':
            error_response["debug_info"] = {
                "traceback": error_details,
                "event": event
            }
            
        return build_response(500, error_response)
