import json
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Process SQS messages for async visual asset generation.
    Triggered by EventBridge when campaign analysis completes.
    """
    try:
        print(f"Received SQS event: {json.dumps(event)}")
        
        # Process each SQS record
        for record in event.get('Records', []):
            process_campaign_completion(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Successfully processed visual asset requests'})
        }
        
    except Exception as e:
        print(f"Error processing visual asset requests: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_campaign_completion(record):
    """
    Process a single campaign completion record from SQS.
    """
    try:
        # Parse the EventBridge event from SQS message
        message_body = json.loads(record['body'])
        
        # If this came from EventBridge, the actual event is in the 'detail' field
        if 'detail' in message_body:
            event_detail = json.loads(message_body['detail'])
        else:
            event_detail = message_body
        
        campaign_id = event_detail.get('campaign_id')
        campaign_data = event_detail.get('campaign_data', {})
        context_data = event_detail.get('context_data', {})
        
        if not campaign_id:
            print("Warning: No campaign_id found in event")
            return
        
        print(f"Processing visual assets for campaign: {campaign_id}")
        
        # Update campaign status to indicate visual asset generation started
        update_campaign_status(campaign_id, 'generating_visuals')
        
        # Invoke the existing visual asset generator Lambda
        visual_assets = invoke_visual_asset_generator(campaign_data, context_data)
        
        # Update campaign status with visual assets
        update_campaign_status_with_assets(campaign_id, 'completed', visual_assets)
        
        print(f"Successfully generated visual assets for campaign: {campaign_id}")
        
    except Exception as e:
        print(f"Error processing campaign completion for record: {str(e)}")
        # Update campaign status to indicate failure
        campaign_id = extract_campaign_id_from_record(record)
        if campaign_id:
            update_campaign_status(campaign_id, 'visual_generation_failed', str(e))
        raise

def invoke_visual_asset_generator(campaign_data, context_data):
    """
    Invoke the existing visual asset generator Lambda function.
    """
    try:
        visual_asset_function_name = os.environ.get('VISUAL_ASSET_GENERATOR_FUNCTION_NAME')
        if not visual_asset_function_name:
            raise Exception("VISUAL_ASSET_GENERATOR_FUNCTION_NAME environment variable not set")
        
        # Build payload for visual asset generator
        payload = {
            'campaign_data': {
                'campaign_id': context_data.get('campaign_id', 'unknown'),
                'product_name': context_data.get('product', {}).get('name', 'Unknown Product'),
                'description': context_data.get('product', {}).get('description', ''),
                'target_audience': context_data.get('target_audience', {}),
                'key_features': extract_key_features(campaign_data),
                'brand_tone': determine_brand_tone(campaign_data, context_data)
            },
            'asset_types': ['video_scripts', 'social_images', 'thumbnails', 'ad_creatives']
        }
        
        # Invoke the visual asset generator Lambda
        response = lambda_client.invoke(
            FunctionName=visual_asset_function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            return response_payload
        else:
            raise Exception(f"Visual asset generator failed: {response_payload}")
    
    except Exception as e:
        print(f"Error invoking visual asset generator: {str(e)}")
        raise

def extract_key_features(campaign_data):
    """
    Extract key features from campaign data for visual asset generation.
    """
    try:
        content = campaign_data.get('content', '')
        
        # Simple feature extraction - look for bullet points or numbered lists
        features = []
        if isinstance(content, str):
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or any(line.startswith(f'{i}.') for i in range(1, 10)):
                    feature = line.lstrip('-•0123456789. ').strip()
                    if feature and len(feature) > 10:  # Only meaningful features
                        features.append(feature)
        
        # Return top 5 features or default features
        return features[:5] if features else ['High Quality', 'User Friendly', 'Innovative Design']
    
    except Exception as e:
        print(f"Error extracting key features: {str(e)}")
        return ['High Quality', 'User Friendly', 'Innovative Design']

def determine_brand_tone(campaign_data, context_data):
    """
    Determine brand tone from campaign data and context.
    """
    try:
        # Look for tone indicators in campaign data
        content = str(campaign_data.get('content', '')).lower()
        
        if 'professional' in content or 'business' in content:
            return 'professional'
        elif 'fun' in content or 'playful' in content or 'engaging' in content:
            return 'playful'
        elif 'luxury' in content or 'premium' in content:
            return 'luxury'
        elif 'friendly' in content or 'approachable' in content:
            return 'friendly'
        else:
            return 'professional'  # Default tone
    
    except Exception as e:
        print(f"Error determining brand tone: {str(e)}")
        return 'professional'

def update_campaign_status(campaign_id, status, error_message=None):
    """
    Update campaign status in DynamoDB.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            print("Warning: CAMPAIGN_STATUS_TABLE_NAME not set")
            return
        
        table = dynamodb.Table(table_name)
        
        update_expression = 'SET #status = :status, updated_at = :updated_at'
        expression_attribute_names = {'#status': 'status'}
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_expression += ', error_message = :error_message'
            expression_attribute_values[':error_message'] = error_message
        
        table.update_item(
            Key={'campaign_id': campaign_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(f"Updated campaign status: {campaign_id} - {status}")
    
    except Exception as e:
        print(f"Error updating campaign status: {str(e)}")

def update_campaign_status_with_assets(campaign_id, status, visual_assets):
    """
    Update campaign status with visual assets data.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            print("Warning: CAMPAIGN_STATUS_TABLE_NAME not set")
            return
        
        table = dynamodb.Table(table_name)
        
        table.update_item(
            Key={'campaign_id': campaign_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, visual_assets = :visual_assets',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat(),
                ':visual_assets': visual_assets
            }
        )
        
        print(f"Updated campaign with visual assets: {campaign_id}")
    
    except Exception as e:
        print(f"Error updating campaign with visual assets: {str(e)}")

def extract_campaign_id_from_record(record):
    """
    Extract campaign ID from SQS record for error handling.
    """
    try:
        message_body = json.loads(record['body'])
        if 'detail' in message_body:
            event_detail = json.loads(message_body['detail'])
            return event_detail.get('campaign_id')
        else:
            return message_body.get('campaign_id')
    except Exception:
        return None