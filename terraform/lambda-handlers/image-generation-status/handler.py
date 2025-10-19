import json
import os
import boto3
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda function to check image generation status.
    Invoked by API Gateway with request_id in path parameters.

    Expected API Gateway path: /images/{request_id}
    
    Returns status of image generation from DynamoDB:
    - 'pending': Image generation is in progress
    - 'completed': Image has been generated and stored in S3
    - 'failed': Image generation failed
    - 'not_found': No record exists for this request_id
    """
    try:
        print(f"Received event: {json.dumps(event)}")

        # Extract request_id from path parameters
        path_parameters = event.get('pathParameters', {})
        request_id = path_parameters.get('request_id', '') if path_parameters else None

        if not request_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required parameter: request_id in path'
                })
            }

        print(f"Checking status for request_id: {request_id}")

        # Check generation status in DynamoDB
        status_info = get_image_generation_status(request_id)

        if not status_info.get('exists'):
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'request_id': request_id,
                    'status': 'not_found',
                    'message': 'No generation record found for this request_id'
                })
            }

        # Return status based on current generation state
        status = status_info.get('status', 'unknown')

        if status == 'completed':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'request_id': request_id,
                    'status': 'completed',
                    's3_key': status_info.get('s3_key'),
                    's3_url': status_info.get('s3_url'),
                    'user_id': status_info.get('user_id'),
                    'prompt': status_info.get('prompt'),
                    'style': status_info.get('style'),
                    'aspect_ratio': status_info.get('aspect_ratio'),
                    'updated_at': status_info.get('updated_at'),
                    'message': 'Image generated successfully'
                })
            }

        elif status == 'pending':
            return {
                'statusCode': 202,
                'body': json.dumps({
                    'success': True,
                    'request_id': request_id,
                    'status': 'pending',
                    'message': 'Image generation is in progress, please check again later'
                })
            }

        elif status == 'failed':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': False,
                    'request_id': request_id,
                    'status': 'failed',
                    'error': status_info.get('error', 'Image generation failed'),
                    'updated_at': status_info.get('updated_at'),
                    'message': 'Image generation failed, you can retry by submitting a new request'
                })
            }

        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': False,
                    'request_id': request_id,
                    'status': status,
                    'message': f'Unknown status: {status}'
                })
            }

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def get_image_generation_status(request_id):
    """
    Retrieve image generation status from DynamoDB.

    Args:
        request_id (str): Unique request identifier

    Returns:
        dict: Status information with keys:
            - exists (bool): Whether the request exists in DB
            - status (str): Status if exists ('pending', 'completed', 'failed')
            - s3_key (str): S3 key if completed
            - user_id (str): User identifier
            - prompt (str): Original prompt
            - style (str): Style used
            - aspect_ratio (str): Aspect ratio used
            - error (str): Error message if failed
            - updated_at (str): Last update timestamp
    """
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'generated_images')
        table = dynamodb.Table(table_name)

        print(f"Querying DynamoDB table '{table_name}' for request_id: {request_id}")

        response = table.get_item(Key={'request_id': request_id})

        if 'Item' in response:
            item = response['Item']
            print(f"Found item in DynamoDB: {json.dumps(item, default=str)}")

            return {
                'exists': True,
                'status': item.get('status', 'unknown'),
                's3_key': item.get('s3_key'),
                's3_url': item.get('s3_url'),
                'user_id': item.get('user_id'),
                'prompt': item.get('prompt'),
                'style': item.get('style'),
                'aspect_ratio': item.get('aspect_ratio'),
                'error': item.get('error'),
                'updated_at': item.get('updated_at')
            }

        print(f"No item found in DynamoDB for request_id: {request_id}")
        return {'exists': False}

    except Exception as e:
        print(f"Error querying DynamoDB: {str(e)}")
        return {
            'exists': False,
            'error': str(e)
        }
