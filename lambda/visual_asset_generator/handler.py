import json
import boto3
import os
import uuid
import base64
import urllib.request
import urllib.parse
import time
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for visual asset generation.
    
    Gen        # Retry mechanism for image generation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = bedrock_runtime.invoke_model(
                    modelId='amazon.titan-image-generator-v1',
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        'taskType': 'TEXT_IMAGE',
                        'textToImageParams': {
                            'text': image_prompt,
                            'negativeText': 'low quality, blurry'
                        },
                        'imageGenerationConfig': {
                            'numberOfImages': 1,
                            'quality': 'standard',
                            'cfgScale': 8.0,
                            'height': height,
                            'width': width,
                            'seed': 42 + attempt  # Different seed per attempt
                        }
                    })
                )
                break  # Success, exit retry loop
            except Exception as e:
                if 'ThrottlingException' in str(e) and attempt < max_retries - 1:
                    print(f"Throttling on attempt {attempt + 1}, waiting...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e, thumbnails, social media posts, and ad creatives
    based on campaign data and product analysis.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check if this is a Bedrock agent invocation
        if 'actionGroup' in event and 'function' in event:
            return handle_bedrock_agent_invocation(event, context)
        else:
            # Direct invocation
            return handle_direct_invocation(event, context)
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_error_response(f"Visual asset generation failed: {str(e)}")

def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        function_name = event.get('function')
        parameters = event.get('parameters', {})
        
        print(f"Bedrock agent function: {function_name}")
        print(f"Parameters: {json.dumps(parameters)}")
        
        if function_name == 'generate_visual_assets':
            return handle_visual_asset_generation(parameters, context)
        else:
            return create_bedrock_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in handle_bedrock_agent_invocation: {str(e)}")
        return create_bedrock_error_response(f"Bedrock agent invocation failed: {str(e)}")

def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation."""
    try:
        return handle_visual_asset_generation(event, context)
    except Exception as e:
        print(f"Error in handle_direct_invocation: {str(e)}")
        return create_error_response(f"Direct invocation failed: {str(e)}")

def handle_visual_asset_generation(parameters, context):
    """Generate comprehensive visual assets for campaign."""
    try:
        # Extract parameters
        campaign_data = parameters.get('campaign_data', {})
        product_data = parameters.get('product_data', {})
        s3_image_key = parameters.get('s3_image_key', '')
        content_requirements = parameters.get('content_requirements', {})
        target_markets = parameters.get('target_markets', [])
        
        campaign_id = campaign_data.get('campaign_id', str(uuid.uuid4()))
        
        print(f"Generating visual assets for campaign: {campaign_id}")
        
        generated_assets = {
            "campaign_id": campaign_id,
            "generated_at": datetime.utcnow().isoformat(),
            "videos": {},
            "images": {}
        }
        
        # Step 1: Generate Video Content (Scripts & Thumbnails)
        if content_requirements.get('generate_videos', True):
            print("Generating video content...")
            video_assets = generate_video_content(campaign_data, product_data, target_markets)
            generated_assets['videos'] = video_assets
        
        # Step 2: Generate Image Content (Social Posts & Ad Creatives)
        if content_requirements.get('generate_images', True):
            print("Generating image content...")
            image_assets = generate_image_content(campaign_data, product_data, s3_image_key, target_markets)
            generated_assets['images'] = image_assets
        
        # Step 3: Store metadata in DynamoDB
        store_asset_metadata(campaign_id, generated_assets, context)
        
        return create_success_response({
            'campaign_id': campaign_id,
            'generated_assets': generated_assets,
            'asset_count': {
                'video_scripts': len(generated_assets['videos'].get('scripts', [])),
                'thumbnails': len(generated_assets['videos'].get('thumbnails', [])),
                'social_posts': len(generated_assets['images'].get('social_posts', [])),
                'ad_creatives': len(generated_assets['images'].get('ad_creatives', []))
            },
            'processing_time': f"{context.get_remaining_time_in_millis() / 1000:.1f}s"
        })
        
    except Exception as e:
        print(f"Error in handle_visual_asset_generation: {str(e)}")
        return create_error_response(f"Visual asset generation failed: {str(e)}")

def generate_video_content(campaign_data, product_data, target_markets):
    """Generate video scripts and thumbnails using Bedrock."""
    try:
        video_assets = {
            "scripts": [],
            "thumbnails": []
        }
        
        platforms = ['tiktok', 'instagram_reels', 'youtube_shorts', 'youtube']
        product_name = product_data.get('name', campaign_data.get('product_name', 'Product'))
        
        # Generate platform-specific video scripts
        for platform in platforms:
            script_data = generate_video_script(platform, product_name, campaign_data, target_markets)
            if script_data:
                video_assets['scripts'].append(script_data)
        
        # Generate video thumbnails with staggered execution
        for i, platform in enumerate(['youtube', 'tiktok', 'instagram']):
            if i > 0:
                time.sleep(1)  # Stagger requests to avoid throttling
            thumbnail_data = generate_video_thumbnail(platform, product_name, campaign_data)
            if thumbnail_data:
                video_assets['thumbnails'].append(thumbnail_data)
        
        return video_assets
        
    except Exception as e:
        print(f"Error generating video content: {str(e)}")
        return {"scripts": [], "thumbnails": [], "error": str(e)}

def generate_video_script(platform, product_name, campaign_data, target_markets):
    """Generate platform-specific video scripts using Claude."""
    try:
        platform_specs = {
            'tiktok': {
                'duration': '15-30s',
                'style': 'Fast-paced, trendy, hook within 3 seconds',
                'structure': 'Hook → Demo → CTA',
                'music': 'Trending audio recommended'
            },
            'instagram_reels': {
                'duration': '15-30s', 
                'style': 'Visually appealing, lifestyle-focused',
                'structure': 'Visual hook → Product integration → Lifestyle benefit',
                'music': 'Upbeat, lifestyle music'
            },
            'youtube_shorts': {
                'duration': '60s',
                'style': 'Educational or entertaining',
                'structure': 'Problem → Solution → Demo → CTA',
                'music': 'Background music, voice-over friendly'
            },
            'youtube': {
                'duration': '3-5 minutes',
                'style': 'Detailed, informative',
                'structure': 'Intro → Problem → Solution → Demo → Benefits → CTA',
                'music': 'Subtle background music'
            }
        }
        
        spec = platform_specs.get(platform, platform_specs['tiktok'])
        
        # Get cultural context if available
        cultural_context = ""
        if target_markets:
            cultural_context = f"Target markets: {', '.join(target_markets)}. Adapt content for cultural relevance."
        
        script_prompt = f"""
        Create a {platform} video script for {product_name}.
        
        Platform: {platform}
        Duration: {spec['duration']}
        Style: {spec['style']}
        Structure: {spec['structure']}
        
        Product Details:
        - Name: {product_name}
        - Key Benefits: {campaign_data.get('key_benefits', ['High quality', 'Great value', 'Easy to use'])}
        - Target Audience: {campaign_data.get('target_audience', 'General consumers')}
        - Unique Selling Points: {campaign_data.get('usp', 'Premium quality at affordable price')}
        
        {cultural_context}
        
        Requirements:
        1. Start with a strong hook that grabs attention immediately
        2. Include specific visual cues and camera directions
        3. Natural, conversational tone
        4. Clear call-to-action
        5. Trending elements appropriate for {platform}
        6. Include music/audio suggestions
        7. Optimize for mobile viewing
        
        Format your response as a structured script with:
        - Scene descriptions
        - Dialogue/voiceover
        - Visual cues
        - Timing markers
        - Music suggestions
        """
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [
                    {
                        'role': 'user',
                        'content': script_prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        script_content = response_body['content'][0]['text']
        
        # Store script as text file in S3
        script_key = f"generated-assets/{campaign_data.get('campaign_id', 'default')}/videos/scripts/{platform}_script.txt"
        s3_client.put_object(
            Bucket=os.environ['S3_ASSETS_BUCKET'],
            Key=script_key,
            Body=script_content.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'platform': platform,
                'product': product_name,
                'duration': spec['duration']
            }
        )
        
        script_url = f"https://{os.environ['S3_ASSETS_BUCKET']}.s3.{os.environ.get('REGION', 'eu-west-1')}.amazonaws.com/{script_key}"
        
        return {
            "platform": platform,
            "duration": spec['duration'],
            "script": script_content,
            "script_url": script_url,
            "visual_cues": extract_visual_cues(script_content),
            "music_suggestion": spec['music'],
            "structure": spec['structure']
        }
        
    except Exception as e:
        print(f"Error generating {platform} script: {str(e)}")
        return None

def generate_video_thumbnail(platform, product_name, campaign_data):
    """Generate video thumbnails using Bedrock Titan Image Generator."""
    try:
        # Using Titan Image Generator supported dimensions only
        platform_specs = {
            'youtube': {'width': 1024, 'height': 1024, 'style': 'Bold text, high contrast, clickable'},
            'tiktok': {'width': 1024, 'height': 1024, 'style': 'Vertical, mobile-first, trendy'},  # Use square for now
            'instagram': {'width': 1024, 'height': 1024, 'style': 'Square, aesthetic, lifestyle'}
        }
        
        spec = platform_specs.get(platform, platform_specs['youtube'])
        
        # Shortened prompt for Titan Image Generator (max 512 chars)
        thumbnail_prompt = f"Professional {platform} thumbnail for {product_name}. High contrast, vibrant colors, product focus. Clean modern background. Commercial quality."
        
        # Retry mechanism for image generation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = bedrock_runtime.invoke_model(
                    modelId='amazon.titan-image-generator-v1',
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        'taskType': 'TEXT_IMAGE',
                        'textToImageParams': {
                            'text': thumbnail_prompt,
                            'negativeText': 'low quality, blurry, distorted'
                        },
                        'imageGenerationConfig': {
                            'numberOfImages': 1,
                            'quality': 'standard',
                            'cfgScale': 8.0,
                            'height': spec['height'],
                            'width': spec['width'],
                            'seed': 42 + attempt  # Different seed per attempt
                        }
                    })
                )
                break  # Success, exit retry loop
            except Exception as e:
                if 'ThrottlingException' in str(e) and attempt < max_retries - 1:
                    print(f"Throttling on attempt {attempt + 1}, waiting...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e
        
        response_body = json.loads(response['body'].read())
        image_bytes = base64.b64decode(response_body['images'][0])
        
        # Store thumbnail in S3
        thumbnail_key = f"generated-assets/{campaign_data.get('campaign_id', 'default')}/videos/thumbnails/{platform}_thumbnail.jpg"
        s3_client.put_object(
            Bucket=os.environ['S3_ASSETS_BUCKET'],
            Key=thumbnail_key,
            Body=image_bytes,
            ContentType='image/jpeg',
            Metadata={
                'platform': platform,
                'product': product_name,
                'dimensions': f"{spec['width']}x{spec['height']}"
            }
        )
        
        thumbnail_url = f"https://{os.environ['S3_ASSETS_BUCKET']}.s3.{os.environ.get('REGION', 'eu-west-1')}.amazonaws.com/{thumbnail_key}"
        
        return {
            "platform": platform,
            "thumbnail_url": thumbnail_url,
            "title_overlay": campaign_data.get('headline', f'Best {product_name} 2024!'),
            "dimensions": f"{spec['width']}x{spec['height']}",
            "format": "JPG"
        }
        
    except Exception as e:
        print(f"Error generating {platform} thumbnail: {str(e)}")
        return None

def generate_image_content(campaign_data, product_data, s3_image_key, target_markets):
    """Generate social media posts and ad creatives."""
    try:
        image_assets = {
            "social_posts": [],
            "ad_creatives": [],
            "infographics": []
        }
        
        product_name = product_data.get('name', campaign_data.get('product_name', 'Product'))
        
        # Generate social media posts for different platforms with staggered execution
        social_platforms = ['instagram', 'facebook', 'twitter', 'linkedin']
        for i, platform in enumerate(social_platforms):
            if i > 0:
                time.sleep(1)  # Stagger requests to avoid throttling
            post_data = generate_social_media_post(platform, product_name, campaign_data)
            if post_data:
                image_assets['social_posts'].append(post_data)
        
        # Generate ad creatives in different formats with staggered execution
        ad_formats = ['square_1024x1024', 'landscape_1152x896', 'portrait_1024x1024']
        for i, format_type in enumerate(ad_formats):
            if i > 0:
                time.sleep(1)  # Stagger requests to avoid throttling
            ad_data = generate_ad_creative(format_type, product_name, campaign_data)
            if ad_data:
                image_assets['ad_creatives'].append(ad_data)
        
        return image_assets
        
    except Exception as e:
        print(f"Error generating image content: {str(e)}")
        return {"social_posts": [], "ad_creatives": [], "error": str(e)}

def generate_social_media_post(platform, product_name, campaign_data):
    """Generate platform-specific social media posts."""
    try:
        # Using Titan Image Generator supported dimensions only
        platform_specs = {
            'instagram': {'size': '1024x1024', 'style': 'Aesthetic, lifestyle-focused, visually appealing'},
            'facebook': {'size': '1024x1024', 'style': 'Community-focused, engaging, shareable'},
            'twitter': {'size': '1024x1024', 'style': 'Concise, news-worthy, conversation-starting'},
            'linkedin': {'size': '1024x1024', 'style': 'Professional, business-focused, value-driven'}
        }
        
        spec = platform_specs.get(platform, platform_specs['instagram'])
        width, height = map(int, spec['size'].split('x'))
        
        # Generate caption using Claude
        caption_prompt = f"""
        Create a {platform} post caption for {product_name}.
        
        Style: {spec['style']}
        Product: {product_name}
        Key Benefits: {campaign_data.get('key_benefits', ['Quality', 'Value', 'Convenience'])}
        Target Audience: {campaign_data.get('target_audience', 'General consumers')}
        
        Requirements:
        - Platform-appropriate tone and style
        - Engaging hook in first line
        - Include relevant hashtags (8-12 for Instagram, 2-3 for others)
        - Call-to-action appropriate for {platform}
        - Keep within platform character limits
        
        Format: Return just the caption text with hashtags.
        """
        
        caption_response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': caption_prompt}]
            })
        )
        
        caption_body = json.loads(caption_response['body'].read())
        caption_text = caption_body['content'][0]['text']
        
        # Shortened prompt for Titan Image Generator (max 512 chars)
        image_prompt = f"Professional {platform} post for {product_name}. Product focus, modern background, positive mood. High quality commercial photo."
        
        image_response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-image-generator-v1',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'taskType': 'TEXT_IMAGE',
                'textToImageParams': {
                    'text': image_prompt,
                    'negativeText': 'low quality, cluttered, unprofessional, blurry'
                },
                'imageGenerationConfig': {
                    'numberOfImages': 1,
                    'quality': 'standard',
                    'cfgScale': 8.0,
                    'height': height,
                    'width': width,
                    'seed': 42
                }
            })
        )
        
        image_body = json.loads(image_response['body'].read())
        image_bytes = base64.b64decode(image_body['images'][0])
        
        # Store in S3
        image_key = f"generated-assets/{campaign_data.get('campaign_id', 'default')}/images/social-posts/{platform}_post.jpg"
        s3_client.put_object(
            Bucket=os.environ['S3_ASSETS_BUCKET'],
            Key=image_key,
            Body=image_bytes,
            ContentType='image/jpeg',
            Metadata={
                'platform': platform,
                'product': product_name,
                'dimensions': spec['size']
            }
        )
        
        image_url = f"https://{os.environ['S3_ASSETS_BUCKET']}.s3.{os.environ.get('REGION', 'eu-west-1')}.amazonaws.com/{image_key}"
        
        # Extract hashtags from caption
        hashtags = [word for word in caption_text.split() if word.startswith('#')]
        
        return {
            "platform": platform,
            "image_url": image_url,
            "caption": caption_text,
            "hashtags": hashtags,
            "dimensions": spec['size'],
            "format": "JPG"
        }
        
    except Exception as e:
        print(f"Error generating {platform} post: {str(e)}")
        return None

def generate_ad_creative(format_type, product_name, campaign_data):
    """Generate ad creatives in different formats."""
    try:
        # Using Titan Image Generator supported dimensions only
        format_specs = {
            'square_1024x1024': {'width': 1024, 'height': 1024, 'name': 'Square', 'use': 'Instagram feed, Facebook'},
            'landscape_1152x896': {'width': 1152, 'height': 896, 'name': 'Landscape', 'use': 'Facebook ads, LinkedIn'},
            'portrait_1024x1024': {'width': 1024, 'height': 1024, 'name': 'Portrait', 'use': 'Instagram Stories, TikTok ads'}  # Use square for now
        }
        
        spec = format_specs.get(format_type, format_specs['square_1080x1080'])
        
        # Generate headline using Claude
        headline_prompt = f"""
        Create a compelling ad headline for {product_name}.
        
        Product: {product_name}
        Key Benefits: {campaign_data.get('key_benefits', ['Quality', 'Value'])}
        Target Audience: {campaign_data.get('target_audience', 'General consumers')}
        
        Requirements:
        - Maximum 5-7 words
        - Action-oriented and compelling
        - Highlights main benefit
        - Creates urgency or desire
        
        Examples: "Transform Your Morning Routine", "Discover Premium Quality", "Upgrade Your Lifestyle"
        
        Return just the headline text.
        """
        
        headline_response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 100,
                'messages': [{'role': 'user', 'content': headline_prompt}]
            })
        )
        
        headline_body = json.loads(headline_response['body'].read())
        headline_text = headline_body['content'][0]['text'].strip().strip('"')
        
        # Shortened prompt for Titan Image Generator (max 512 chars)
        ad_prompt = f"Professional ad for {product_name}. {spec['name']} format. Product hero shot, clean background, commercial quality, professional lighting."
        
        # Retry mechanism for image generation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ad_response = bedrock_runtime.invoke_model(
                    modelId='amazon.titan-image-generator-v1',
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        'taskType': 'TEXT_IMAGE',
                        'textToImageParams': {
                            'text': ad_prompt,
                            'negativeText': 'low quality, amateur, blurry'
                        },
                        'imageGenerationConfig': {
                            'numberOfImages': 1,
                            'quality': 'standard',
                            'cfgScale': 8.0,
                            'height': spec['height'],
                            'width': spec['width'],
                            'seed': 42 + attempt  # Different seed per attempt
                        }
                    })
                )
                break  # Success, exit retry loop
            except Exception as e:
                if 'ThrottlingException' in str(e) and attempt < max_retries - 1:
                    print(f"Throttling on attempt {attempt + 1}, waiting...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e
        
        ad_body = json.loads(ad_response['body'].read())
        image_bytes = base64.b64decode(ad_body['images'][0])
        
        # Store in S3
        ad_key = f"generated-assets/{campaign_data.get('campaign_id', 'default')}/images/ad-creatives/{format_type}_ad.jpg"
        s3_client.put_object(
            Bucket=os.environ['S3_ASSETS_BUCKET'],
            Key=ad_key,
            Body=image_bytes,
            ContentType='image/jpeg',
            Metadata={
                'format': format_type,
                'product': product_name,
                'headline': headline_text
            }
        )
        
        ad_url = f"https://{os.environ['S3_ASSETS_BUCKET']}.s3.{os.environ.get('REGION', 'eu-west-1')}.amazonaws.com/{ad_key}"
        
        return {
            "format": format_type,
            "image_url": ad_url,
            "headline": headline_text,
            "dimensions": f"{spec['width']}x{spec['height']}",
            "use_case": spec['use'],
            "format_name": spec['name']
        }
        
    except Exception as e:
        print(f"Error generating {format_type} ad: {str(e)}")
        return None

def extract_visual_cues(script_content):
    """Extract visual cues from video script."""
    try:
        visual_keywords = ['close-up', 'wide shot', 'zoom in', 'pan', 'transition', 'cut to', 'fade in', 'fade out']
        lines = script_content.lower().split('\n')
        visual_cues = []
        
        for line in lines:
            for keyword in visual_keywords:
                if keyword in line:
                    visual_cues.append(line.strip())
                    break
        
        return visual_cues[:5]  # Return top 5 visual cues
    except:
        return ["Close-up shot", "Transition effect"]

def store_asset_metadata(campaign_id, generated_assets, context):
    """Store asset metadata in DynamoDB."""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME')
        if not table_name:
            print("Warning: DynamoDB table name not configured")
            return
        
        table = dynamodb.Table(table_name)
        
        # Convert floats to Decimals for DynamoDB compatibility
        def convert_floats(obj):
            if isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(v) for v in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            else:
                return obj
        
        metadata_record = {
            'intelligence_id': f"visual_assets_{campaign_id}",
            'campaign_id': campaign_id,
            'asset_metadata': convert_floats(generated_assets),
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id,
            'analysis_type': 'visual_assets'
        }
        
        table.put_item(Item=metadata_record)
        print(f"Stored asset metadata for campaign: {campaign_id}")
        
    except Exception as e:
        print(f"Error storing asset metadata: {str(e)}")

def create_success_response(data):
    """Create a success response."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'data': data
        })
    }

def create_error_response(error_message):
    """Create an error response."""
    return {
        'statusCode': 400,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }

def create_bedrock_error_response(error_message, api_path='unknown'):
    """Create a Bedrock agent error response."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'visual-assets',
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