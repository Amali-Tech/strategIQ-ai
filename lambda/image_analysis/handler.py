import json
import boto3
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for image analysis using Amazon Rekognition.
    
    Can be invoked by:
    1. Bedrock agent (action group) - Returns Bedrock format response with product_id
    2. Intent parser Lambda - Returns JSON response with product_id
    
    Analyzes product images and stores results in DynamoDB with analysis_status='image_analyzed'
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
        
        if action_group != 'image-analysis':
            return create_error_response(f"Invalid action group: {action_group}")
        
        if function_name == 'analyze_product_image':
            return handle_image_analysis(parameters, context)
        else:
            return create_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_error_response(f"Internal error: {str(e)}")


def handle_image_analysis(parameters, context):
    """
    Handle product image analysis using Rekognition.
    
    Args:
        parameters: Dictionary containing product_info and s3_info (JSON strings or dicts)
        context: Lambda context object
        
    Returns:
        Dictionary with analysis results and product_id
    """
    try:
        # Get raw parameters
        product_info_raw = parameters.get('product_info', {})
        s3_info_raw = parameters.get('s3_info', {})
        
        # Parse JSON strings if needed
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
        
        # Ensure we have dicts
        if not isinstance(product_info, dict):
            product_info = {}
        if not isinstance(s3_info, dict):
            s3_info = {}
        
        # Extract values with fallbacks
        product_name = (product_info.get('name') or '').strip() or "Analyzed Product"
        s3_key = (s3_info.get('key') or '').strip()
        
        # Validate S3 key
        if not s3_key:
            return create_error_response("S3 key is required")
        
        bucket = s3_info.get('bucket') or os.environ.get('S3_BUCKET_NAME', 'degenerals-mi-dev-images')
        
        # Verify S3 object exists
        try:
            s3.head_object(Bucket=bucket, Key=s3_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return create_error_response(f"Image not found in S3: s3://{bucket}/{s3_key}")
            raise
        
        # Perform Rekognition analysis
        analysis_results = analyze_image_with_rekognition(bucket, s3_key)
        
        # Create structured data record
        product_record = create_product_record(
            product_info=product_info,
            s3_info={'bucket': bucket, 'key': s3_key},
            analysis_results=analysis_results,
            request_id=context.aws_request_id
        )
        
        # Save to DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'products')
        save_product_to_dynamodb(table_name, product_record)
        
        # Return structured response with product_id
        response_data = {
            'success': True,
            'product_id': product_record['product_id'],
            'product_name': product_name,
            'detected_labels': analysis_results['labels'][:10],
            'analysis_status': 'image_analyzed',
            'timestamp': product_record['created_at']
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
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
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=50,
            MinConfidence=60
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
        'product_name': product_info.get('name', 'Unknown Product'),
        'product_description': product_info.get('description', ''),
        'product_category': product_info.get('category', ''),
        's3_bucket': s3_info['bucket'],
        's3_key': s3_info['key'],
        's3_url': f"s3://{s3_info['bucket']}/{s3_info['key']}",
        'image_labels': convert_floats(analysis_results['labels']),
        'total_labels_detected': analysis_results['total_labels'],
        'high_confidence_labels_count': analysis_results['high_confidence_count'],
        'rekognition_metadata': analysis_results['rekognition_response_metadata'],
        'created_at': timestamp,
        'updated_at': timestamp,
        'lambda_request_id': request_id,
        'analysis_status': 'image_analyzed'  # Key indicator that image has been analyzed
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
                    
                    if prop_name == 'product_info':
                        try:
                            json_body['product_info'] = json.loads(prop_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid product_info JSON", api_path)
                    
                    elif prop_name == 's3_info':
                        try:
                            json_body['s3_info'] = json.loads(prop_value)
                        except json.JSONDecodeError:
                            return create_bedrock_error_response(f"Invalid s3_info JSON", api_path)
        
        if not json_body:
            return create_bedrock_error_response("Could not extract valid JSON from Bedrock request", api_path)
        
        print(f"Constructed JSON body: {json.dumps(json_body)}")
        
        if function_name == 'analyze_product_image' or api_path == '/analyze-product-image':
            result = handle_image_analysis(json_body, context)
            
            if result.get('statusCode') == 200:
                body_data = json.loads(result['body'])
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': 'image-analysis',
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
        return create_bedrock_error_response(f"Internal error: {str(e)}", "/analyze-product-image")


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
