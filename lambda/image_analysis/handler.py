import json
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for image analysis using Amazon Rekognition.
    Analyzes        if function_name == 'analyze_product_image' or api_path == '/analyze-product-image':
            # Convert to internal format
            product_info = parameters.get('product_info', {})
            s3_info = parameters.get('s3_info', {})
            
            internal_params = {
                'product_info': {
                    'name': product_info.get('name', '') if isinstance(product_info, dict) else '',
                    'description': product_info.get('description', '') if isinstance(product_info, dict) else '',
                    'category': product_info.get('category', '') if isinstance(product_info, dict) else ''
                },
                's3_info': {
                    'bucket': s3_info.get('bucket', '') if isinstance(s3_info, dict) else '',
                    'key': s3_info.get('key', '') if isinstance(s3_info, dict) else ''
                }
            }es and stores structured data in DynamoDB.
    
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
        
        if action_group != 'image-analysis':
            return create_error_response(f"Invalid action group: {action_group}")
        
        if function_name == 'analyze_product_image':
            return handle_image_analysis(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_bedrock_error_response(f"Internal error: {str(e)}")

def handle_image_analysis(parameters, context):
    """
    Handle product image analysis using Rekognition.
    
    Args:
        parameters: Dictionary containing product_info and s3_info
        context: Lambda context object
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Validate required parameters
        product_info_raw = parameters.get('product_info', {})
        s3_info_raw = parameters.get('s3_info', {})
        
        # Parse JSON strings if they are strings
        if isinstance(product_info_raw, str):
            try:
                product_info = json.loads(product_info_raw)
            except json.JSONDecodeError:
                return create_error_response("Invalid product_info JSON format")
        else:
            product_info = product_info_raw
            
        if isinstance(s3_info_raw, str):
            try:
                s3_info = json.loads(s3_info_raw)
            except json.JSONDecodeError:
                return create_error_response("Invalid s3_info JSON format")
        else:
            s3_info = s3_info_raw
        
        if not product_info.get('name'):
            return create_error_response("Product name is required")
        
        if not s3_info.get('bucket') or not s3_info.get('key'):
            return create_error_response("S3 bucket and key are required")
        
        bucket = s3_info['bucket']
        key = s3_info['key']
        
        # Verify S3 object exists
        try:
            s3.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return create_error_response(f"Image not found in S3: s3://{bucket}/{key}")
            raise
        
        # Perform Rekognition analysis
        analysis_results = analyze_image_with_rekognition(bucket, key)
        
        # Create structured data record
        product_record = create_product_record(
            product_info=product_info,
            s3_info=s3_info,
            analysis_results=analysis_results,
            request_id=context.aws_request_id
        )
        
        # Save to DynamoDB
        table_name = "products"
        save_product_to_dynamodb(table_name, product_record)
        
        # Return structured response for Bedrock agent
        return create_success_response({
            'product_id': product_record['product_id'],
            'product_name': product_info['name'],
            'detected_labels': analysis_results['labels'][:10],  # Top 10 labels
            'confidence_summary': {
                'high_confidence_labels': [
                    label for label in analysis_results['labels'] 
                    if label['confidence'] >= 80
                ],
                'total_labels_detected': len(analysis_results['labels'])
            },
            'analysis_timestamp': product_record['created_at'],
            'storage_location': f"DynamoDB table: {table_name}",
            'recommendations': generate_campaign_recommendations(analysis_results['labels'])
        })
        
    except Exception as e:
        print(f"Error in handle_image_analysis: {str(e)}")
        return create_error_response(f"Image analysis failed: {str(e)}")

def analyze_image_with_rekognition(bucket, key):
    """
    Use Amazon Rekognition to analyze the image and detect labels.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Detect labels in the image
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=50,  # Get up to 50 labels
            MinConfidence=60  # Minimum confidence threshold
        )
        
        # Process labels
        labels = []
        for label in response['Labels']:
            label_data = {
                'name': label['Name'],
                'confidence': round(label['Confidence'], 2),
                'categories': [cat['Name'] for cat in label.get('Categories', [])],
                'instances': len(label.get('Instances', []))
            }
            labels.append(label_data)
        
        # Sort by confidence
        labels.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'labels': labels,
            'total_labels': len(labels),
            'high_confidence_count': len([l for l in labels if l['confidence'] >= 80]),
            'rekognition_response_metadata': {
                'request_id': response['ResponseMetadata']['RequestId']
            }
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Rekognition error: {error_code} - {error_message}")
        raise Exception(f"Rekognition analysis failed: {error_message}")

def create_product_record(product_info, s3_info, analysis_results, request_id):
    """
    Create a structured product record for DynamoDB storage.
    
    Args:
        product_info: Product information
        s3_info: S3 location information
        analysis_results: Rekognition analysis results
        request_id: Lambda request ID
        
    Returns:
        Dictionary representing the product record
    """
    from decimal import Decimal
    
    product_id = str(uuid.uuid4())
    
    # Extract user_id from S3 key path (uploads/{user_id}/...)
    s3_key_parts = s3_info['key'].split('/')
    user_id = s3_key_parts[1] if len(s3_key_parts) > 1 else 'anonymous'
    
    timestamp = datetime.utcnow().isoformat()
    
    # Convert float values to Decimal for DynamoDB compatibility
    def convert_floats(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(v) for v in obj]
        return obj
    
    return {
        'product_id': product_id,
        'user_id': user_id,
        'product_name': product_info['name'],
        'product_description': product_info.get('description', ''),
        'product_category': product_info.get('category', ''),
        's3_bucket': s3_info['bucket'],
        's3_key': s3_info['key'],
        's3_url': f"s3://{s3_info['bucket']}/{s3_info['key']}",
        'labels': convert_floats(analysis_results['labels']),
        'total_labels_detected': analysis_results['total_labels'],
        'high_confidence_labels_count': analysis_results['high_confidence_count'],
        'rekognition_metadata': analysis_results['rekognition_response_metadata'],
        'created_at': timestamp,
        'lambda_request_id': request_id,
        'analysis_status': 'completed'
    }

def save_product_to_dynamodb(table_name, record):
    """
    Save product record to DynamoDB table.
    
    Args:
        table_name: DynamoDB table name
        record: Product record to save
    """
    try:
        table = dynamodb.Table(table_name)
        table.put_item(Item=record)
        print(f"Successfully saved product record {record['product_id']} to DynamoDB")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"DynamoDB error: {error_code} - {error_message}")
        raise Exception(f"Failed to save product to DynamoDB: {error_message}")

def generate_campaign_recommendations(labels):
    """
    Generate basic campaign recommendations based on detected labels.
    
    Args:
        labels: List of detected labels with confidence scores
        
    Returns:
        Dictionary with campaign recommendations
    """
    high_confidence_labels = [label for label in labels if label['confidence'] >= 80]
    
    recommendations = {
        'primary_visual_elements': [label['name'] for label in high_confidence_labels[:5]],
        'suggested_hashtags': [f"#{label['name'].lower().replace(' ', '')}" for label in high_confidence_labels[:8]],
        'content_themes': extract_content_themes(high_confidence_labels),
        'platform_suitability': assess_platform_suitability(high_confidence_labels)
    }
    
    return recommendations

def extract_content_themes(labels):
    """Extract content themes based on label categories."""
    themes = set()
    for label in labels:
        for category in label.get('categories', []):
            if category in ['Technology', 'Fashion', 'Food and Drink', 'Sports', 'Nature']:
                themes.add(category.lower())
    return list(themes)

def assess_platform_suitability(labels):
    """Assess platform suitability based on visual elements."""
    label_names = [label['name'].lower() for label in labels]
    
    suitability = {
        'Instagram': 'High' if any(term in ' '.join(label_names) for term in ['person', 'fashion', 'food', 'lifestyle']) else 'Medium',
        'TikTok': 'High' if any(term in ' '.join(label_names) for term in ['person', 'action', 'dynamic']) else 'Medium',
        'LinkedIn': 'High' if any(term in ' '.join(label_names) for term in ['technology', 'business', 'professional']) else 'Low',
        'Facebook': 'Medium',  # Generally suitable for most content
    }
    
    return suitability

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
    """Create an error response for direct invocation."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }

def create_bedrock_error_response(error_message, api_path='/analyze-product-image'):
    """Create a Bedrock agent compatible error response."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'image-analysis',
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

def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        # Extract the request body content directly
        request_body = event.get('requestBody', {})
        content = request_body.get('content', {})
        
        # Parse function and API path
        function_name = event.get('function', '')
        api_path = event.get('apiPath', '')
        
        print(f"Function: {function_name}, API Path: {api_path}")
        print(f"Content: {json.dumps(content, default=str)}")
        
        # Handle the specific Bedrock agent format with properties array
        json_body = None
        if 'application/json' in content and isinstance(content['application/json'], dict):
            app_json = content['application/json']
            if 'properties' in app_json:
                # Convert properties array to proper JSON structure
                json_body = {}
                for prop in app_json['properties']:
                    prop_name = prop.get('name')
                    prop_value = prop.get('value', '')
                    
                    if prop_name == 'product_info':
                        # Parse the product_info string
                        try:
                            # Fix the JSON format
                            fixed_value = '{' + prop_value + '}'
                            json_body['product_info'] = json.loads(fixed_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid product_info format: {prop_value}", api_path)
                    
                    elif prop_name == 's3_info':
                        # Parse the s3_info string
                        try:
                            # Fix the JSON format
                            fixed_value = '{' + prop_value + '}'
                            json_body['s3_info'] = json.loads(fixed_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid s3_info format: {prop_value}", api_path)
        
        if not json_body:
            return create_bedrock_error_response("Could not extract valid JSON from Bedrock request", api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body, default=str)}")
        
        if function_name == 'analyze_product_image' or api_path in ['/analyze-image', '/analyze-product-image']:
            # Validate required fields
            product_info = json_body.get('product_info')
            s3_info = json_body.get('s3_info')
            
            if not product_info:
                return create_bedrock_error_response("product_info is required", api_path)
            if not s3_info:
                return create_bedrock_error_response("s3_info is required", api_path)
            
            # Call the analysis function with the extracted parameters
            result = handle_image_analysis(json_body, context)
            
            # Convert response to Bedrock format
            if result.get('statusCode') == 200:
                body_data = json.loads(result['body'])
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': 'image-analysis',
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
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return create_bedrock_error_response(f"Processing error: {str(e)}")