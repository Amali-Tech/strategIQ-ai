import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('vom-table')
bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_comments_for_post(post_id):
    try:
        response = table.query(
            KeyConditionExpression=Key('PK').eq(post_id) & Key('SK').begins_with('COMMENT#')
        )
        return response['Items']
    except Exception as e:
        print(f"Error querying comments for post {post_id}: {str(e)}")
        return []

def update_post_with_action_items(post_id, action_items, comments_count):
    """
    Updates an existing post record with generated action items.
    
    Args:
        post_id: The ID of the post to update
        action_items: Dictionary containing the generated action items
        comments_count: Number of comments analyzed for this post
    
    Returns:
        Boolean indicating success/failure of the update
    """
    try:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        response = table.update_item(
            Key={
                'PK': post_id,
                'SK': 'POST'
            },
            UpdateExpression="SET action_items_summary = :summary, positive_actions = :pos, negative_actions = :neg, action_items_generated_at = :timestamp, comments_analyzed_count = :count",
            ExpressionAttributeValues={
                ':summary': action_items.get('summary', ''),
                ':pos': action_items.get('positive_actions', []),
                ':neg': action_items.get('negative_actions', []),
                ':timestamp': timestamp,
                ':count': comments_count
            }
        )
        print(f"Successfully updated post {post_id} with action items")
        return True
        
    except Exception as e:
        print(f"Error updating post {post_id} with action items: {str(e)}")
        return False

def generate_action_items(all_comments_info):
    """
    Invokes an AWS Bedrock model to generate management action items grouped into positive and negative items
    based on the sentiment analysis of cosmetic post comments.

    Args:
        all_comments_info: A list of dictionaries containing details about comments,
                          including 'comment_text', 'sentiment', and 'sentiment_score'.

    Returns:
        A dictionary containing the generated action items
    """
    if not all_comments_info:
        print("No comments data provided for action item generation")
        return {"positive_actions": [], "negative_actions": [], "summary": "No comments to analyze"}
    
    print(f"Generating action items for {len(all_comments_info)} comments")
    
    # Prepare the prompt with all comments data
    comments_summary = json.dumps(all_comments_info, indent=2, default=decimal_default)
    
    prompt = f"""
    Based on the following sentiment analysis results for cosmetic product comments:

    Comments Data: {comments_summary}

    Please analyze these comments and provide management action items. Group the action items into:
    1. **Positive Actions**: Actions to leverage positive feedback and sentiment
    2. **Negative Actions**: Actions to address negative feedback and concerns

    For each action item, be specific and actionable for a cosmetic product management team.

    Format your response as JSON with the following structure:
    {{
        "summary": "Brief overview of the overall sentiment and key insights (2-3 sentences)",
        "positive_actions": [
            "Specific action item 1 based on positive feedback",
            "Specific action item 2 based on positive feedback",
            ...
        ],
        "negative_actions": [
            "Specific action item 1 to address negative feedback", 
            "Specific action item 2 to address negative feedback",
            ...
        ]
    }}
    """

    bedrock_body = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.7
        }
    }

    try:
        print("Calling Bedrock to generate action items...")
        # Try using the cross-region inference profile first
        bedrock_response = bedrock.invoke_model(
            body=json.dumps(bedrock_body),
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            accept='application/json',
            contentType='application/json'
        )
        print("Bedrock call successful")
    except Exception as e:
        print(f"Primary Bedrock model failed: {str(e)}")
        # Fallback to Nova Lite if Nova Pro is not available
        try:
            print("Trying fallback model...")
            bedrock_response = bedrock.invoke_model(
                body=json.dumps(bedrock_body),
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                accept='application/json',
                contentType='application/json'
            )
            print("Fallback Bedrock call successful")
        except Exception as fallback_error:
            print(f"Fallback Bedrock model also failed: {str(fallback_error)}")
            # Return default structure if both attempts fail
            return {
                "summary": "Unable to generate AI-powered action items due to service unavailability",
                "positive_actions": ["Review positive feedback manually", "Continue current successful practices"],
                "negative_actions": ["Investigate negative feedback manually", "Address customer concerns promptly"],
                "error": f"Bedrock unavailable: {str(e)} | Fallback error: {str(fallback_error)}"
            }

    try:
        bedrock_result = json.loads(bedrock_response['body'].read())
        bedrock_content = bedrock_result['content'][0]['text']
        
        # Parse the JSON response from Bedrock
        action_items = json.loads(bedrock_content)
        print("Successfully parsed Bedrock response")
        return action_items
        
    except json.JSONDecodeError as parse_error:
        print(f"Failed to parse Bedrock response as JSON: {str(parse_error)}")
        print(f"Raw response: {bedrock_content}")
        # Return a structured response even if parsing fails
        return {
            "summary": "Action items generated but response format was unexpected",
            "positive_actions": ["Review positive feedback patterns"],
            "negative_actions": ["Address negative feedback concerns"], 
            "raw_response": bedrock_content,
            "parse_error": str(parse_error)
        }
    except Exception as e:
        print(f"Error processing Bedrock response: {str(e)}")
        return {
            "summary": "Failed to process action items generation",
            "positive_actions": [],
            "negative_actions": [],
            "error": str(e)
        }

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    processed_posts = 0
    successful_updates = []
    failed_updates = []
    total_comments_processed = 0
    
    try:
        posts_to_process = []
        
        if 'Records' in event:
            for record in event['Records']:
                if 'body' in record:
                    jsonBody = json.loads(record['body'])
                else:
                    jsonBody = record
                
                if 'affected_posts' in jsonBody:
                    posts_to_process.extend(jsonBody['affected_posts'])
        else:
            if 'affected_posts' in event:
                posts_to_process.extend(event['affected_posts'])
        
        # Process each post individually
        for post_info in posts_to_process:
            post_id = post_info['post_id']
            print(f"\n=== Processing post: {post_id} ===")
            
            try:
                # Get comments for this specific post
                comments = get_comments_for_post(post_id)
                
                if comments:
                    print(f"Found {len(comments)} comments for post {post_id}")
                    
                    # Extract comment information for this post
                    post_comments_info = []
                    for comment in comments:
                        comment_info = {
                            "comment_text": comment.get('comment_text', 'N/A'),
                            "sentiment": comment.get('sentiment', 'N/A'),
                            "sentiment_score": comment.get('sentiment_score', {})
                        }
                        post_comments_info.append(comment_info)
                    
                    # Generate action items for this specific post
                    print(f"Generating action items for post {post_id}")
                    action_items = generate_action_items(post_comments_info)
                    print(f"Action items generated for {post_id}: {json.dumps(action_items, indent=2)}")
                    
                    # Update the post record with action items
                    update_success = update_post_with_action_items(post_id, action_items, len(comments))
                    
                    if update_success:
                        successful_updates.append({
                            'post_id': post_id,
                            'comments_processed': len(comments),
                            'action_items': action_items
                        })
                    else:
                        failed_updates.append({
                            'post_id': post_id,
                            'comments_processed': len(comments),
                            'error': 'Failed to update post record'
                        })
                    
                    total_comments_processed += len(comments)
                    
                else:
                    print(f"No comments found for post {post_id}")
                    failed_updates.append({
                        'post_id': post_id,
                        'comments_processed': 0,
                        'error': 'No comments found'
                    })
                
                processed_posts += 1
                
            except Exception as post_error:
                print(f"Error processing post {post_id}: {str(post_error)}")
                failed_updates.append({
                    'post_id': post_id,
                    'error': str(post_error)
                })
    
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing event',
                'error': str(e)
            })
        }
    
    print(f"\n=== PROCESSING SUMMARY ===")
    print(f"Total posts processed: {processed_posts}")
    print(f"Successfully updated posts: {len(successful_updates)}")
    print(f"Failed updates: {len(failed_updates)}")
    print(f"Total comments processed: {total_comments_processed}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Successfully processed posts with action items',
            'posts_processed': processed_posts,
            'successful_updates': len(successful_updates),
            'failed_updates': len(failed_updates),
            'total_comments_processed': total_comments_processed,
            'successful_posts': successful_updates,
            'failed_posts': failed_updates
        })
    }
