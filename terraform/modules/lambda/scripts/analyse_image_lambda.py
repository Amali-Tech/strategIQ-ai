import json
import logging
import traceback
import base64
import hashlib

# Configure logging first
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    import boto3
    import uuid
    import os
    from datetime import datetime
    from decimal import Decimal
    from urllib.parse import unquote_plus
    
    logger.info("All imports successful")
except Exception as e:
    logger.error(f"Import error: {str(e)}")
    logger.error(traceback.format_exc())
    raise

class ProductImageAnalyzer:
    def __init__(self, region_name='us-east-1'):
        """Initialize AWS clients"""
        try:
            logger.info(f"Initializing ProductImageAnalyzer with region: {region_name}")
            self.s3_client = boto3.client('s3', region_name=region_name)
            self.rekognition_client = boto3.client('rekognition', region_name=region_name)
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AWS clients: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def _to_decimal(self, value):
        """Recursively convert floats to Decimal for DynamoDB"""
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, list):
            return [self._to_decimal(v) for v in value]
        if isinstance(value, dict):
            return {k: self._to_decimal(v) for k, v in value.items()}
        return value

    def get_s3_metadata(self, bucket_name: str, object_key: str) -> dict:
        """Get metadata from S3 object"""
        try:
            logger.info(f"Getting S3 metadata for: s3://{bucket_name}/{object_key}")
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            metadata = response.get('Metadata', {})
            logger.info(f"S3 metadata retrieved: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Error getting S3 metadata: {str(e)}")
            return {}

    def analyze_product_image(self, bucket_name: str, object_key: str) -> dict:
        """Analyze product image using Amazon Rekognition"""
        try:
            logger.info(f"Analyzing image: s3://{bucket_name}/{object_key}")
            
            # Check file extension and log it
            file_extension = object_key.lower().split('.')[-1]
            logger.info(f"Image file extension: {file_extension}")
            
            # Verify the image exists in S3
            try:
                s3_response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
                logger.info(f"S3 object info - Content-Type: {s3_response.get('ContentType', 'unknown')}, Size: {s3_response.get('ContentLength', 'unknown')} bytes")
            except Exception as s3_error:
                logger.error(f"Error accessing S3 object: {str(s3_error)}")
                raise
            
            # Detect labels (objects, scenes, activities, etc.)
            logger.info("Starting Rekognition detect_labels...")
            labels_response = self.rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': object_key
                    }
                },
                MaxLabels=20,
                MinConfidence=50
            )
            logger.info(f"Labels detected: {len(labels_response.get('Labels', []))}")
            
            # Detect text in image (product names, prices, etc.)
            logger.info("Starting Rekognition detect_text...")
            try:
                text_response = self.rekognition_client.detect_text(
                    Image={
                        'S3Object': {
                            'Bucket': bucket_name,
                            'Name': object_key
                        }
                    }
                )
                logger.info(f"Text detections: {len(text_response.get('TextDetections', []))}")
            except Exception as text_error:
                logger.error(f"Error in detect_text: {str(text_error)}")
                # Continue with empty text response if text detection fails
                text_response = {'TextDetections': []}
            
            # Detect moderation labels (check for inappropriate content)
            logger.info("Starting Rekognition detect_moderation_labels...")
            try:
                moderation_response = self.rekognition_client.detect_moderation_labels(
                    Image={
                        'S3Object': {
                            'Bucket': bucket_name,
                            'Name': object_key
                        }
                    },
                    MinConfidence=50
                )
                logger.info(f"Moderation labels: {len(moderation_response.get('ModerationLabels', []))}")
            except Exception as mod_error:
                logger.error(f"Error in detect_moderation_labels: {str(mod_error)}")
                # Continue with empty moderation response if moderation detection fails
                moderation_response = {'ModerationLabels': []}
            
            # Process labels
            product_labels = []
            for label in labels_response['Labels']:
                product_labels.append({
                    'name': label['Name'],
                    'confidence': float(label['Confidence']),
                    'categories': [cat['Name'] for cat in label.get('Categories', [])]
                })
            
            # Extract text information
            detected_text = []
            for text_detection in text_response['TextDetections']:
                if text_detection['Type'] == 'WORD':
                    detected_text.append({
                        'text': text_detection['DetectedText'],
                        'confidence': float(text_detection['Confidence'])
                    })
            
            # Check for inappropriate content
            is_appropriate = len(moderation_response['ModerationLabels']) == 0
            
            analysis_results = {
                'product_labels': product_labels,
                'detected_text': detected_text,
                'is_appropriate_content': is_appropriate,
                'moderation_labels': [
                    {
                        'name': label['Name'],
                        'confidence': float(label['Confidence'])
                    } for label in moderation_response['ModerationLabels']
                ],
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def extract_product_info(self, analysis_results: dict) -> dict:
        """Extract and categorize product information from Rekognition results"""
        product_info = {
            'product_categories': [],
            'product_attributes': [],
            'brand_text': [],
            'price_text': [],
            'other_text': []
        }
        
        # Categorize labels into product types
        product_categories = set()
        product_attributes = []
        
        for label in analysis_results['product_labels']:
            label_name = label['name'].lower()
            confidence = label['confidence']
            
            # Common product categories
            if any(category in label_name for category in ['clothing', 'apparel', 'fashion', 'shirt', 'dress', 'pants']):
                product_categories.add('Fashion')
            elif any(category in label_name for category in ['electronics', 'phone', 'computer', 'device', 'laptop']):
                product_categories.add('Electronics')
            elif any(category in label_name for category in ['food', 'beverage', 'drink', 'snack']):
                product_categories.add('Food & Beverage')
            elif any(category in label_name for category in ['book', 'magazine', 'publication']):
                product_categories.add('Books & Media')
            elif any(category in label_name for category in ['furniture', 'chair', 'table', 'sofa']):
                product_categories.add('Furniture')
            elif any(category in label_name for category in ['toy', 'game']):
                product_categories.add('Toys & Games')
            elif any(category in label_name for category in ['shoe', 'boot', 'sneaker']):
                product_categories.add('Footwear')
            
            product_attributes.append({
                'attribute': label['name'],
                'confidence': confidence
            })
        
        product_info['product_categories'] = list(product_categories)
        product_info['product_attributes'] = product_attributes
        
        # Categorize detected text
        for text_item in analysis_results['detected_text']:
            text = text_item['text']
            
            # Simple pattern matching for prices
            if any(char in text for char in ['$', '€', '£', '¥']) or 'price' in text.lower():
                product_info['price_text'].append(text)
            # Check for potential brand names (capitalized words)
            elif text.isupper() and len(text) > 2:
                product_info['brand_text'].append(text)
            else:
                product_info['other_text'].append(text)
        
        return product_info

    def store_in_dynamodb(self, table_name: str, bucket_name: str, object_key: str, 
                         analysis_results: dict, product_info: dict, s3_metadata: dict) -> str:
        """Store product image analysis results in DynamoDB"""
        try:
            logger.info(f"Storing data in DynamoDB table: {table_name}")
            table = self.dynamodb.Table(table_name)
            
            # Generate unique ID for the record
            item_id = str(uuid.uuid4())
            image_hash = base64.urlsafe_b64encode(hashlib.sha256(object_key.encode()).digest()).decode('utf-8').rstrip('=')

            # Prepare item for DynamoDB
            item = {
                'id': item_id,
                'bucket_name': bucket_name,
                'imageHash': image_hash,
                's3_url': f"s3://{bucket_name}/{object_key}",
                'public_url': f"https://{bucket_name}.s3.amazonaws.com/{object_key}",
                'analysis_timestamp': analysis_results['analysis_timestamp'],
                'user_product_details': s3_metadata.get('product-details', ''),
                'user_product_category': s3_metadata.get('product-category', ''),
                'platform': s3_metadata.get('platform', ''),
                'ai_product_categories': product_info['product_categories'],
                'product_attributes': product_info['product_attributes'],
                'detected_text': product_info['brand_text'] + product_info['price_text'] + product_info['other_text'],
                'brand_text': product_info['brand_text'],
                'price_text': product_info['price_text'],
                'is_appropriate_content': analysis_results['is_appropriate_content'],
                'moderation_labels': analysis_results['moderation_labels'],
                'labels_count': len(analysis_results['product_labels']),
                'text_count': len(analysis_results['detected_text']),
                'categories_count': len(product_info['product_categories']),
                'raw_analysis': json.dumps(analysis_results),
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Convert floats to Decimal for DynamoDB
            item = self._to_decimal(item)
            
            # Put item in DynamoDB
            table.put_item(Item=item)
            logger.info(f"Data stored successfully in DynamoDB with ID: {item_id}")
            return item_id
            
        except Exception as e:
            logger.error(f"Error storing data in DynamoDB: {str(e)}")
            logger.error(traceback.format_exc())
            raise

def lambda_handler(event, context):
    """
    Lambda function handler for S3 trigger events
    This function is triggered when an image is uploaded to S3
    """
    
    logger.info("=== LAMBDA FUNCTION STARTED ===")
    logger.info(f"Event received: {json.dumps(event, default=str)}")
    
    try:
        # Environment variables
        DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'product-analysis-table')
        logger.info(f"Using DynamoDB table: {DYNAMODB_TABLE}")
        
        # Validate environment
        if not DYNAMODB_TABLE or DYNAMODB_TABLE == 'product-analysis-table':
            logger.warning("DYNAMODB_TABLE_NAME environment variable not set, using default")
        
        # Initialize analyzer
        logger.info("Initializing ProductImageAnalyzer...")
        analyzer = ProductImageAnalyzer()
        logger.info("ProductImageAnalyzer initialized successfully")
        
        processed_records = []
        
        # Validate event structure
        if 'Records' not in event:
            logger.error("No 'Records' found in event")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid event structure',
                    'message': 'No Records found in event'
                })
            }
        
        logger.info(f"Processing {len(event['Records'])} records")
        
        # Process each record in the event
        for i, record in enumerate(event['Records']):
            logger.info(f"=== PROCESSING RECORD {i+1}/{len(event['Records'])} ===")
            
            try:
                # Extract S3 event information
                bucket_name = record['s3']['bucket']['name']
                object_key = unquote_plus(record['s3']['object']['key'])
                event_name = record['eventName']
                
                logger.info(f"Processing {event_name} for s3://{bucket_name}/{object_key}")
                
                # Only process ObjectCreated events
                if not event_name.startswith('ObjectCreated'):
                    logger.info(f"Skipping non-creation event: {event_name}")
                    continue
                
                # Check if it's an image file
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                file_extension = object_key.lower().split('.')[-1] if '.' in object_key else 'no-extension'
                logger.info(f"File extension detected: .{file_extension}")
                
                is_image = any(object_key.lower().endswith(ext) for ext in image_extensions)
                logger.info(f"Is this an image file? {is_image}")
                
                if not is_image:
                    logger.info(f"Skipping non-image file: {object_key}")
                    continue
                
                logger.info(f"Processing image file: {object_key}")
                
                # Step 0: Get S3 metadata (product details, category, platform)
                logger.info("Step 0: Getting S3 metadata...")
                s3_metadata = analyzer.get_s3_metadata(bucket_name, object_key)
                logger.info("S3 metadata retrieval completed")
                
                # Step 1: Analyze image with Rekognition
                logger.info("Step 1: Analyzing image with Rekognition...")
                analysis_results = analyzer.analyze_product_image(bucket_name, object_key)
                logger.info("Rekognition analysis completed successfully")
                
                # Step 2: Extract product information
                logger.info("Step 2: Extracting product information...")
                product_info = analyzer.extract_product_info(analysis_results)
                logger.info("Product information extraction completed")
                
                # Step 3: Store in DynamoDB
                logger.info("Step 3: Storing results in DynamoDB...")
                item_id = analyzer.store_in_dynamodb(
                    DYNAMODB_TABLE, 
                    bucket_name, 
                    object_key, 
                    analysis_results, 
                    product_info,
                    s3_metadata
                )
                logger.info("DynamoDB storage completed successfully")
                
                # Record successful processing
                processed_records.append({
                    'bucket': bucket_name,
                    'key': object_key,
                    'item_id': item_id,
                    'user_description': s3_metadata.get('product-details', ''),
                    'user_product_category': s3_metadata.get('product-category', ''),
                    'platform': s3_metadata.get('platform', ''),
                    'ai_categories': product_info['product_categories'],
                    'labels_count': len(analysis_results['product_labels']),
                    'text_count': len(analysis_results['detected_text']),
                    'is_appropriate': analysis_results['is_appropriate_content'],
                    'success': True
                })
                
                logger.info(f"Successfully processed image: {object_key}")
                
            except Exception as e:
                logger.error(f"Error processing record {i+1}: {str(e)}")
                logger.error(traceback.format_exc())
                # Continue processing other records even if one fails
                processed_records.append({
                    'bucket': bucket_name if 'bucket_name' in locals() else 'unknown',
                    'key': object_key if 'object_key' in locals() else 'unknown',
                    'error': str(e),
                    'success': False
                })
        
        logger.info(f"=== LAMBDA FUNCTION COMPLETED - Processed {len(processed_records)} records ===")
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Image analysis completed',
                'processed_records': processed_records,
                'total_processed': len(processed_records)
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        }