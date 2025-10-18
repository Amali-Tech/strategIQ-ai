import json
import boto3
import base64
import uuid
from datetime import datetime
import os
from botocore.exceptions import ClientError

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to generate images using Amazon Nova Canvas via Bedrock.
    Triggered by SQS queue messages containing image generation requests.

    Expected SQS message format:
    {
        "prompt": "Detailed description of the image to generate",
        "style": "Optional style preset (natural, vivid, etc.)",
        "aspect_ratio": "Optional aspect ratio (16:9, 1:1, etc.)",
        "user_id": "User identifier for tracking",
        "request_id": "Unique request identifier"
    }
    """
    print(f"Received event: {json.dumps(event)}")

    # Process SQS messages
    for record in event.get('Records', []):
        try:
            # Parse the SQS message body
            message_body = json.loads(record['body'])
            print(f"Processing message: {json.dumps(message_body)}")

            # Extract parameters from message
            prompt = message_body.get('prompt', '')
            if not prompt:
                print("Error: No prompt provided in message")
                continue

            style = message_body.get('style', 'natural')
            aspect_ratio = message_body.get('aspect_ratio', '1:1')
            user_id = message_body.get('user_id', 'anonymous')
            request_id = message_body.get('request_id', str(uuid.uuid4()))

            # Generate the image
            image_data = generate_image_with_nova_canvas(
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio
            )

            if image_data:
                # Store the image in S3
                s3_key = store_image_in_s3(
                    image_data=image_data,
                    user_id=user_id,
                    request_id=request_id,
                    prompt=prompt
                )

                print(f"Successfully generated and stored image: {s3_key}")

                # Optional: Store metadata in DynamoDB for tracking
                store_generation_metadata(
                    request_id=request_id,
                    user_id=user_id,
                    prompt=prompt,
                    s3_key=s3_key,
                    style=style,
                    aspect_ratio=aspect_ratio
                )
            else:
                print(f"Failed to generate image for request {request_id}")

        except json.JSONDecodeError as e:
            print(f"Error parsing message body: {str(e)}")
            continue
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            # Continue processing other messages even if one fails
            continue

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Image generation processing completed',
            'processed_messages': len(event.get('Records', []))
        })
    }

def generate_image_with_nova_canvas(prompt, style='natural', aspect_ratio='1:1'):
    """
    Generate an image using Amazon Nova Canvas via Bedrock.

    Args:
        prompt (str): Text description of the image to generate
        style (str): Style preset (natural, vivid, etc.)
        aspect_ratio (str): Aspect ratio for the generated image

    Returns:
        bytes: Generated image data, or None if generation failed
    """
    try:
        # Map aspect ratio to Nova Canvas format
        aspect_ratio_map = {
            '1:1': '1:1',
            '16:9': '16:9',
            '9:16': '9:16',
            '4:3': '4:3',
            '3:4': '3:4'
        }

        # Ensure aspect ratio is valid
        if aspect_ratio not in aspect_ratio_map:
            aspect_ratio = '1:1'

        # Prepare the request for Nova Canvas
        request_body = {
            'taskType': 'TEXT_IMAGE',
            'textToImageParams': {
                'text': prompt,
                'negativeText': 'blurry, low quality, distorted, ugly, poorly drawn'
            },
            'imageGenerationConfig': {
                'numberOfImages': 1,
                'quality': 'standard',
                'width': 1024 if aspect_ratio == '1:1' else 1280,
                'height': 1024 if aspect_ratio == '1:1' else (720 if aspect_ratio == '16:9' else 1280),
                'cfgScale': 7.0,
                'seed': None  # Random seed for variety
            }
        }

        # Add style-specific parameters if needed
        if style == 'vivid':
            request_body['imageGenerationConfig']['cfgScale'] = 8.0
        elif style == 'natural':
            request_body['imageGenerationConfig']['cfgScale'] = 6.0

        print(f"Invoking Nova Canvas with prompt: {prompt[:100]}...")

        # Invoke the model
        response = bedrock_client.invoke_model(
            modelId='amazon.nova-canvas-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        # Parse the response
        response_body = json.loads(response['body'].read())

        # Extract the base64-encoded image
        if 'images' in response_body and len(response_body['images']) > 0:
            image_base64 = response_body['images'][0]
            image_data = base64.b64decode(image_base64)
            print(f"Successfully generated image, size: {len(image_data)} bytes")
            return image_data
        else:
            print("No images returned in response")
            return None

    except ClientError as e:
        print(f"Bedrock client error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None

def store_image_in_s3(image_data, user_id, request_id, prompt):
    """
    Store the generated image in S3 bucket.

    Args:
        image_data (bytes): The image data to store
        user_id (str): User identifier
        request_id (str): Unique request identifier
        prompt (str): The prompt used to generate the image

    Returns:
        str: S3 key where the image was stored
    """
    try:
        # Generate S3 key
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Create a safe filename from the prompt (first few words)
        safe_prompt = '_'.join(prompt.split()[:3]).replace('/', '_').replace('\\', '_')[:50]
        s3_key = f"generated/{user_id}/{timestamp}_{request_id}_{safe_prompt}.png"

        # Get bucket name from environment variable
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'degenerals-mi-dev-images')

        # Store the image
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=image_data,
            ContentType='image/png',
            Metadata={
                'user-id': user_id,
                'request-id': request_id,
                'prompt': prompt[:500],  # Limit metadata size
                'generated-at': datetime.now().isoformat()
            }
        )

        print(f"Stored image in S3: s3://{bucket_name}/{s3_key}")
        return s3_key

    except ClientError as e:
        print(f"S3 client error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error storing image in S3: {str(e)}")
        raise

def store_generation_metadata(request_id, user_id, prompt, s3_key, style, aspect_ratio):
    """
    Store generation metadata in DynamoDB for tracking and analytics.

    Args:
        request_id (str): Unique request identifier
        user_id (str): User identifier
        prompt (str): The prompt used
        s3_key (str): S3 key where image is stored
        style (str): Style used for generation
        aspect_ratio (str): Aspect ratio used
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')

        # Get table name from environment
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'generated_images')

        table = dynamodb.Table(table_name)

        # Store metadata
        table.put_item(
            Item={
                'request_id': request_id,
                'user_id': user_id,
                'prompt': prompt,
                's3_key': s3_key,
                'style': style,
                'aspect_ratio': aspect_ratio,
                'generated_at': datetime.now().isoformat(),
                'status': 'completed'
            }
        )

        print(f"Stored metadata for request {request_id}")

    except Exception as e:
        print(f"Error storing metadata (non-critical): {str(e)}")
        # Don't raise exception as this is not critical for the main functionality
