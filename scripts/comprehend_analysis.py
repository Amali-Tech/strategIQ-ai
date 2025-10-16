import json
import boto3
from decimal import Decimal

comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    print(event)
    processed_records = 0
    errors = []
    
    try:
        for record in event['Records']:
            if record['eventName'] != 'INSERT':
                print(f"Skipping {record['eventName']} event")
                continue
                
            try:
                process_comment_record(record)
                processed_records += 1
            except Exception as e:
                error_msg = f"Error processing record {record.get('eventID', 'unknown')}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
        
        print(f"Processed {processed_records} records successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed_records': processed_records,
                'errors': errors
            })
        }
        
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_comment_record(record):
    dynamodb_record = record['dynamodb']
    
    if 'NewImage' not in dynamodb_record:
        print("No NewImage found in record")
        return
    
    new_image = dynamodb_record['NewImage']
    
    if 'comment_text' not in new_image:
        print("No comment_text found in NewImage")
        return
    
    comment_text = new_image['comment_text']['S']
    table_name = record['eventSourceARN'].split('/')[1]
    
    pk = new_image['PK']['S']
    sk = new_image['SK']['S']
    
    print(f"Processing comment: {comment_text[:50]}...")
    
    sentiment_result = analyze_sentiment(comment_text)
    targeted_sentiment_result = analyze_targeted_sentiment(comment_text)
    
    update_dynamodb_record(table_name, pk, sk, sentiment_result, targeted_sentiment_result)

def analyze_sentiment(text):
    try:
        response = comprehend.detect_sentiment(
            Text=text,
            LanguageCode='en'
        )
        return {
            'sentiment': response['Sentiment'],
            'sentiment_score': response['SentimentScore']
        }
    except Exception as e:
        print(f"Error in sentiment analysis: {str(e)}")
        return {
            'sentiment': 'UNKNOWN',
            'sentiment_score': {'Positive': 0, 'Negative': 0, 'Neutral': 0, 'Mixed': 0}
        }

def analyze_targeted_sentiment(text):
    try:
        response = comprehend.detect_targeted_sentiment(
            Text=text,
            LanguageCode='en'
        )
        return {
            'entities': response.get('Entities', [])
        }
    except Exception as e:
        print(f"Error in targeted sentiment analysis: {str(e)}")
        return {
            'entities': []
        }

def update_dynamodb_record(table_name, pk, sk, sentiment_result, targeted_sentiment_result):
    try:
        table = dynamodb.Table(table_name)
        
        update_expression = "SET #sentiment = :sentiment, #sentiment_score = :sentiment_score, #targeted_sentiment = :targeted_sentiment, #processed = :processed"
        expression_attribute_names = {
            '#sentiment': 'sentiment',
            '#sentiment_score': 'sentiment_score',
            '#targeted_sentiment': 'targeted_sentiment',
            '#processed': 'processed'
        }
        expression_attribute_values = {
            ':sentiment': sentiment_result['sentiment'],
            ':sentiment_score': convert_floats_to_decimal(sentiment_result['sentiment_score']),
            ':targeted_sentiment': convert_floats_to_decimal(targeted_sentiment_result['entities']),
            ':processed': True
        }
        
        table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(f"Successfully updated record PK={pk}, SK={sk}")
        
    except Exception as e:
        print(f"Error updating DynamoDB record: {str(e)}")
        raise

def convert_floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    return obj
