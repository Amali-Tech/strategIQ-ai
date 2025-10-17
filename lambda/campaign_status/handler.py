import json
import os
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Handle campaign status API requests.
    Supports GET /api/campaigns/{campaign_id}/status and GET /api/campaigns/status
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Parse route and method
        route_key = event.get('routeKey', '')
        http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        if http_method == 'GET':
            if 'campaign_id' in path_parameters:
                # Get specific campaign status
                campaign_id = path_parameters['campaign_id']
                return get_campaign_status(campaign_id)
            else:
                # List campaigns with optional status filter
                status_filter = query_parameters.get('status')
                limit = int(query_parameters.get('limit', '10'))
                return list_campaigns(status_filter, limit)
        else:
            return create_response(405, {'error': 'Method not allowed'})
    
    except Exception as e:
        print(f"Error handling campaign status request: {str(e)}")
        return create_response(500, {'error': f'Internal server error: {str(e)}'})

def get_campaign_status(campaign_id):
    """
    Get status for a specific campaign.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            return create_response(500, {'error': 'Campaign status table not configured'})
        
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'campaign_id': campaign_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Campaign not found'})
        
        campaign = response['Item']
        
        # Calculate progress percentage based on status
        progress = calculate_progress(campaign['status'])
        
        result = {
            'campaign_id': campaign['campaign_id'],
            'status': campaign['status'],
            'progress': progress,
            'created_at': campaign.get('created_at'),
            'updated_at': campaign.get('updated_at'),
            'context_data': campaign.get('context_data', {}),
            'result_data': campaign.get('result_data'),
            'visual_assets': campaign.get('visual_assets'),
            'error_message': campaign.get('error_message')
        }
        
        # Remove None values
        result = {k: v for k, v in result.items() if v is not None}
        
        return create_response(200, result)
    
    except Exception as e:
        print(f"Error getting campaign status: {str(e)}")
        return create_response(500, {'error': str(e)})

def list_campaigns(status_filter=None, limit=10):
    """
    List campaigns with optional status filter.
    """
    try:
        table_name = os.environ.get('CAMPAIGN_STATUS_TABLE_NAME')
        if not table_name:
            return create_response(500, {'error': 'Campaign status table not configured'})
        
        table = dynamodb.Table(table_name)
        
        if status_filter:
            # Query by status using GSI
            response = table.query(
                IndexName='StatusIndex',
                KeyConditionExpression=Key('status').eq(status_filter),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Scan all campaigns (limited)
            response = table.scan(Limit=limit)
        
        campaigns = []
        for item in response.get('Items', []):
            progress = calculate_progress(item['status'])
            
            campaign_info = {
                'campaign_id': item['campaign_id'],
                'status': item['status'],
                'progress': progress,
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at'),
                'product_name': item.get('context_data', {}).get('product', {}).get('name', 'Unknown'),
                'has_visual_assets': bool(item.get('visual_assets')),
                'error_message': item.get('error_message')
            }
            
            # Remove None values
            campaign_info = {k: v for k, v in campaign_info.items() if v is not None}
            campaigns.append(campaign_info)
        
        # Sort by created_at descending
        campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        result = {
            'campaigns': campaigns,
            'count': len(campaigns),
            'status_filter': status_filter
        }
        
        return create_response(200, result)
    
    except Exception as e:
        print(f"Error listing campaigns: {str(e)}")
        return create_response(500, {'error': str(e)})

def calculate_progress(status):
    """
    Calculate progress percentage based on campaign status.
    """
    status_progress = {
        'processing': 20,
        'analysis_completed': 60,
        'generating_visuals': 80,
        'completed': 100,
        'visual_generation_failed': 60,  # Analysis completed but visuals failed
        'failed': 0
    }
    
    return status_progress.get(status, 0)

def create_response(status_code, body):
    """
    Create a standardized API Gateway response.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body, default=str)  # Handle datetime serialization
    }