import json
import boto3
import uuid
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client('s3')

# Get environment variables
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
PRESIGNED_URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', '3600'))  # Default 1 hour

def lambda_handler(event, context):
    """
    Handle both presigned URL generation and upload status checking
    """
    try:
        # Parse the incoming request
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
        path = event.get('path') or event.get('rawPath', '')
        
        # Handle different routes
        if http_method == 'POST' and '/api/upload/presigned-url' in path:
            return handle_presigned_url_request(event)
        elif http_method == 'GET' and '/api/upload/' in path:
            return handle_upload_status_request(event)
        else:
            return create_response(400, {'error': 'Invalid request'})
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handle_presigned_url_request(event):
    """
    Generate presigned URL for S3 upload
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract required fields
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        file_size = body.get('fileSize')
        user_id = body.get('userId', 'anonymous')
        
        # Validate required fields
        if not file_name or not file_type:
            return create_response(400, {'error': 'fileName and fileType are required'})
        
        # Validate file type (only allow images)
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if file_type not in allowed_types:
            return create_response(400, {'error': f'File type {file_type} not allowed. Allowed types: {allowed_types}'})
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size and file_size > max_size:
            return create_response(400, {'error': f'File size too large. Maximum allowed: {max_size} bytes'})
        
        # Generate unique key for the file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_id = str(uuid.uuid4())
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        image_key = f"uploads/{user_id}/{timestamp}_{upload_id}.{file_extension}"
        
        # Generate presigned URL with regional endpoint to avoid redirects
        region = os.environ.get('AWS_REGION', 'eu-west-1')
        regional_s3_client = boto3.client(
            's3',
            region_name=region,
            config=boto3.session.Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4'
            )
        )
        
        presigned_url = regional_s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': image_key,
                'ContentType': file_type
            },
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        
        # Return response with field names that match frontend expectations
        response_data = {
            'uploadUrl': presigned_url,
            'imageHash': upload_id,  # Using upload_id as imageHash for consistency
            'imageKey': image_key,
            'uploadId': upload_id,
            'expiresIn': PRESIGNED_URL_EXPIRATION,
            'requiredHeaders': {
                'Content-Type': file_type
            }
        }
        
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return create_response(500, {'error': 'Failed to generate presigned URL'})

def handle_upload_status_request(event):
    """
    Check if an image has been uploaded to S3
    """
    try:
        # Extract upload ID from path parameters
        path_parameters = event.get('pathParameters', {})
        upload_id = path_parameters.get('uploadId')
        
        if not upload_id:
            return create_response(400, {'error': 'uploadId is required'})
        
        # Search for the object in S3 using the upload ID
        # We'll need to list objects and check metadata since we don't have the full key
        try:
            # List objects in the uploads folder
            response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix='uploads/',
                MaxKeys=1000
            )
            
            found_object = None
            for obj in response.get('Contents', []):
                # Get object metadata to check upload ID
                try:
                    head_response = s3_client.head_object(
                        Bucket=BUCKET_NAME,
                        Key=obj['Key']
                    )
                    
                    metadata = head_response.get('Metadata', {})
                    if metadata.get('upload-id') == upload_id:
                        found_object = {
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'lastModified': obj['LastModified'].isoformat(),
                            'originalFilename': metadata.get('original-filename'),
                            'userId': metadata.get('user-id')
                        }
                        break
                        
                except ClientError:
                    continue
            
            if found_object:
                response_data = {
                    'success': True,
                    'uploadId': upload_id,
                    'status': 'completed',
                    'imageKey': found_object['key'],
                    'imageUrl': f"https://{BUCKET_NAME}.s3.amazonaws.com/{found_object['key']}",
                    'metadata': {
                        'size': found_object['size'],
                        'lastModified': found_object['lastModified'],
                        'originalFilename': found_object['originalFilename'],
                        'userId': found_object['userId']
                    }
                }
            else:
                response_data = {
                    'success': False,
                    'uploadId': upload_id,
                    'status': 'not_found',
                    'message': 'Upload not found or still in progress'
                }
                
            return create_response(200, response_data)
            
        except ClientError as e:
            print(f"S3 error: {str(e)}")
            return create_response(500, {'error': 'Failed to check upload status'})
            
    except Exception as e:
        print(f"Error checking upload status: {str(e)}")
        return create_response(500, {'error': 'Failed to check upload status'})

def create_response(status_code, body):
    """
    Create HTTP response with proper CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }