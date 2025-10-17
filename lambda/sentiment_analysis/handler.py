import json
import boto3
import os
import uuid
import urllib.request
import urllib.parse
import traceback
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Initialize AWS clients
comprehend = boto3.client('comprehend')
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda handler for sentiment analysis and action items generation.
    
    Searches for content related to a product/brand, analyzes sentiment using AWS Comprehend,
    and uses Bedrock to generate actionable insights.
    
    Handles both direct invocation and Bedrock agent invocation formats.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check if this is a Bedrock agent invocation
        if 'actionGroup' in event and 'function' in event:
            return handle_bedrock_agent_invocation(event, context)
        else:
            # Direct invocation - extract parameters directly
            return handle_direct_invocation(event, context)
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return create_error_response(f"Sentiment analysis failed: {str(e)}")

def handle_bedrock_agent_invocation(event, context):
    """Handle Bedrock agent invocation format."""
    try:
        function_name = event.get('function')
        parameters = event.get('parameters', {})
        
        print(f"Bedrock agent function: {function_name}")
        print(f"Parameters: {json.dumps(parameters)}")
        
        if function_name == 'analyze_sentiment':
            return handle_sentiment_analysis(parameters, context)
        elif function_name == 'generate_action_items':
            return handle_action_items_generation(parameters, context)
        elif function_name == 'comprehensive_sentiment_analysis':
            return handle_comprehensive_sentiment_analysis(parameters, context)
        else:
            return create_bedrock_error_response(f"Unknown function: {function_name}")
            
    except Exception as e:
        print(f"Error in handle_bedrock_agent_invocation: {str(e)}")
        return create_bedrock_error_response(f"Bedrock agent invocation failed: {str(e)}")

def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation."""
    try:
        # Extract parameters from event
        search_query = event.get('search_query')
        product_name = event.get('product_name')
        analysis_type = event.get('analysis_type', 'comprehensive')
        
        if not search_query:
            return create_error_response("search_query is required")
            
        parameters = {
            'search_query': search_query,
            'product_name': product_name or search_query,
            'analysis_type': analysis_type
        }
        
        if analysis_type == 'sentiment_only':
            return handle_sentiment_analysis(parameters, context)
        elif analysis_type == 'action_items_only':
            return handle_action_items_generation(parameters, context)
        else:
            return handle_comprehensive_sentiment_analysis(parameters, context)
            
    except Exception as e:
        print(f"Error in handle_direct_invocation: {str(e)}")
        return create_error_response(f"Direct invocation failed: {str(e)}")

def handle_sentiment_analysis(parameters, context):
    """Perform sentiment analysis on search results and social media content."""
    try:
        search_query = parameters.get('search_query')
        product_name = parameters.get('product_name', search_query)
        
        if not search_query:
            return create_error_response("search_query parameter is required")
        
        print(f"Starting sentiment analysis for: {search_query}")
        
        # Step 1: Search for content related to the product/brand
        search_results = search_for_content(search_query)
        
        # Step 2: Extract comments and engagement data
        content_data = extract_content_and_engagement(search_results)
        
        # Step 3: Perform sentiment analysis using AWS Comprehend
        sentiment_results = analyze_sentiment_with_comprehend(content_data)
        
        # Step 4: Aggregate and structure the results
        analysis_summary = aggregate_sentiment_results(sentiment_results, product_name)
        
        # Step 5: Save to DynamoDB
        analysis_id = str(uuid.uuid4())
        analysis_record = {
            'intelligence_id': analysis_id,  # Use intelligence_id as primary key to match table schema
            'analysis_id': analysis_id,      # Keep analysis_id for backward compatibility
            'search_query': search_query,
            'product_name': product_name,
            'sentiment_results': sentiment_results,
            'analysis_summary': analysis_summary,
            'content_analyzed': len(content_data),
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id,
            'analysis_type': 'sentiment_analysis'
        }
        
        table_name = get_dynamodb_table_name()
        save_analysis_to_dynamodb(table_name, analysis_record)
        
        # Return structured response
        return create_success_response({
            'analysis_id': analysis_id,
            'search_query': search_query,
            'product_name': product_name,
            'sentiment_summary': analysis_summary,
            'content_analyzed': len(content_data),
            'detailed_results': sentiment_results[:10],  # Limit for response size
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': analysis_record['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_sentiment_analysis: {str(e)}")
        return create_error_response(f"Sentiment analysis failed: {str(e)}")

def handle_action_items_generation(parameters, context):
    """Generate action items based on sentiment analysis results."""
    try:
        analysis_id = parameters.get('analysis_id')
        search_query = parameters.get('search_query')
        sentiment_data = parameters.get('sentiment_data')
        
        # If analysis_id is provided, retrieve from DynamoDB
        if analysis_id:
            sentiment_data = retrieve_analysis_from_dynamodb(analysis_id)
        elif search_query:
            # Perform fresh sentiment analysis
            sentiment_params = {'search_query': search_query}
            sentiment_response = handle_sentiment_analysis(sentiment_params, context)
            if sentiment_response['statusCode'] != 200:
                return sentiment_response
            sentiment_data = json.loads(sentiment_response['body'])['data']
        
        if not sentiment_data:
            return create_error_response("sentiment_data, analysis_id, or search_query is required")
        
        print(f"Generating action items for sentiment data")
        
        # Use Bedrock to generate actionable insights
        action_items = generate_action_items_with_bedrock(sentiment_data)
        
        # Prioritize and categorize action items
        structured_actions = structure_action_items(action_items, sentiment_data)
        
        # Save to DynamoDB
        action_id = str(uuid.uuid4())
        action_record = {
            'intelligence_id': action_id,  # Use intelligence_id as primary key
            'analysis_id': action_id,      # Keep analysis_id for backward compatibility
            'source_analysis_id': analysis_id,
            'search_query': sentiment_data.get('search_query'),
            'action_items': structured_actions,
            'generated_actions': action_items,
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id,
            'analysis_type': 'action_items'
        }
        
        table_name = get_dynamodb_table_name()
        save_analysis_to_dynamodb(table_name, action_record)
        
        return create_success_response({
            'action_id': action_id,
            'source_analysis': analysis_id,
            'action_items': structured_actions,
            'generated_insights': action_items,
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': action_record['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_action_items_generation: {str(e)}")
        return create_error_response(f"Action items generation failed: {str(e)}")

def handle_comprehensive_sentiment_analysis(parameters, context):
    """Perform comprehensive sentiment analysis and generate action items in one call."""
    try:
        search_query = parameters.get('search_query')
        product_name = parameters.get('product_name', search_query)
        
        if not search_query:
            return create_error_response("search_query parameter is required")
        
        print(f"Starting comprehensive sentiment analysis for: {search_query}")
        
        # Step 1: Perform sentiment analysis
        sentiment_response = handle_sentiment_analysis(parameters, context)
        if sentiment_response['statusCode'] != 200:
            return sentiment_response
            
        sentiment_data = json.loads(sentiment_response['body'])['data']
        
        # Step 2: Generate action items
        action_params = {'sentiment_data': sentiment_data}
        action_response = handle_action_items_generation(action_params, context)
        if action_response['statusCode'] != 200:
            return action_response
            
        action_data = json.loads(action_response['body'])['data']
        
        # Step 3: Combine results
        comprehensive_id = str(uuid.uuid4())
        comprehensive_record = {
            'intelligence_id': comprehensive_id,  # Use intelligence_id as primary key
            'analysis_id': comprehensive_id,      # Keep analysis_id for backward compatibility
            'search_query': search_query,
            'product_name': product_name,
            'sentiment_analysis': sentiment_data,
            'action_items': action_data,
            'created_at': datetime.utcnow().isoformat(),
            'request_id': context.aws_request_id,
            'analysis_type': 'comprehensive'
        }
        
        table_name = get_dynamodb_table_name()
        save_analysis_to_dynamodb(table_name, comprehensive_record)
        
        return create_success_response({
            'analysis_id': comprehensive_id,
            'search_query': search_query,
            'product_name': product_name,
            'sentiment_analysis': sentiment_data,
            'action_items': action_data,
            'comprehensive_insights': {
                'overall_sentiment': sentiment_data.get('sentiment_summary', {}).get('overall_sentiment'),
                'priority_actions': action_data.get('action_items', {}).get('high_priority', []),
                'key_insights': extract_key_insights(sentiment_data, action_data)
            },
            'storage_location': f"DynamoDB table: {table_name}",
            'timestamp': comprehensive_record['created_at']
        })
        
    except Exception as e:
        print(f"Error in handle_comprehensive_sentiment_analysis: {str(e)}")
        return create_error_response(f"Comprehensive sentiment analysis failed: {str(e)}")

def search_for_content(search_query, max_results=50):
    """Search for content using multiple sources - YouTube, News APIs, and simulated social media."""
    try:
        print(f"Searching for content: {search_query}")
        
        all_results = []
        
        # 1. Search YouTube for video content and comments
        youtube_results = search_youtube_content(search_query, min(max_results // 3, 15))
        all_results.extend(youtube_results)
        
        # 2. Search News API for articles and reviews  
        news_results = search_news_content(search_query, min(max_results // 3, 15))
        all_results.extend(news_results)
        
        # 3. Add some simulated social media content (representing Reddit, Twitter, etc.)
        # In a full production system, you'd integrate with Reddit API, Twitter API, etc.
        social_results = get_simulated_social_content(search_query, min(max_results // 3, 20))
        all_results.extend(social_results)
        
        print(f"Found {len(all_results)} total content pieces from all sources")
        return all_results[:max_results]
        
    except Exception as e:
        print(f"Error in search_for_content: {str(e)}")
        return []

def search_youtube_content(search_query, max_results=15):
    """Search YouTube for video content related to the query."""
    try:
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            print("YouTube API key not configured, skipping YouTube search")
            return []
        
        # Build YouTube API request
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'maxResults': max_results,
            'key': api_key,
            'type': 'video',
            'safeSearch': 'moderate',
            'order': 'relevance'
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        print(f"YouTube search request for sentiment analysis")
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        youtube_results = []
        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            result = {
                'title': snippet.get('title', ''),
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'source': 'youtube',
                'content': snippet.get('description', '')[:500],  # Limit description length
                'engagement': {
                    'platform': 'youtube',
                    'video_id': item['id']['videoId'],
                    'channel': snippet.get('channelTitle', ''),
                    'published': snippet.get('publishedAt', '')
                }
            }
            youtube_results.append(result)
        
        print(f"Found {len(youtube_results)} YouTube videos")
        return youtube_results
        
    except Exception as e:
        print(f"Error searching YouTube: {str(e)}")
        return []

def search_news_content(search_query, max_results=15):
    """Search for news articles and reviews using a news API."""
    try:
        # You can integrate with NewsAPI, Google News API, or other news sources
        # For this example, we'll simulate news content based on the query
        
        news_results = []
        news_templates = [
            {
                'title_template': f'{search_query} receives mixed reviews from tech experts',
                'content_template': f'Technology reviewers are divided on the latest {search_query}. While some praise its innovative features, others point to areas needing improvement.',
                'source': 'tech_review',
                'sentiment_hint': 'mixed'
            },
            {
                'title_template': f'Consumer reports highlight {search_query} quality concerns',
                'content_template': f'Recent consumer feedback on {search_query} shows concerns about build quality and durability. Users report various issues that may affect long-term satisfaction.',
                'source': 'consumer_report',
                'sentiment_hint': 'negative'
            },
            {
                'title_template': f'{search_query} exceeds expectations in latest market analysis',
                'content_template': f'Market analysts report that {search_query} is performing above expectations, with strong sales figures and positive consumer feedback driving market confidence.',
                'source': 'market_analysis',
                'sentiment_hint': 'positive'
            },
            {
                'title_template': f'Industry experts weigh in on {search_query} impact',
                'content_template': f'Industry professionals discuss the potential impact of {search_query} on the market. Opinions vary from cautious optimism to enthusiastic endorsement.',
                'source': 'industry_news',
                'sentiment_hint': 'neutral'
            }
        ]
        
        for i, template in enumerate(news_templates[:max_results]):
            result = {
                'title': template['title_template'],
                'url': f'https://news-example.com/article/{i+1}',
                'source': template['source'],
                'content': template['content_template'],
                'engagement': {
                    'platform': 'news',
                    'expected_sentiment': template['sentiment_hint'],
                    'article_type': template['source']
                }
            }
            news_results.append(result)
        
        print(f"Generated {len(news_results)} news-style content pieces")
        return news_results
        
    except Exception as e:
        print(f"Error generating news content: {str(e)}")
        return []

def get_simulated_social_content(search_query, max_results=20):
    """Generate simulated social media content for sentiment analysis."""
    try:
        social_results = []
        
        # Simulate various social media post types with different sentiments
        social_templates = [
            {
                'title': f'Just got my {search_query} and I\'m blown away!',
                'content': f'Seriously impressed with this {search_query}. The quality is outstanding and it exceeded all my expectations. Totally worth the investment!',
                'platform': 'twitter',
                'engagement': {'likes': 245, 'retweets': 32, 'comments': 18},
                'sentiment_hint': 'very_positive'
            },
            {
                'title': f'Disappointed with my {search_query} purchase',
                'content': f'Unfortunately, the {search_query} didn\'t live up to the hype. Build quality feels cheap and it broke after just a few weeks. Not recommended.',
                'platform': 'reddit',
                'engagement': {'upvotes': 89, 'downvotes': 12, 'comments': 45},
                'sentiment_hint': 'negative'
            },
            {
                'title': f'{search_query} unboxing - first impressions',
                'content': f'Unboxed the new {search_query} today. First impressions are really positive - great packaging and design. Will post a full review after testing.',
                'platform': 'instagram',
                'engagement': {'likes': 1250, 'comments': 89, 'shares': 156},
                'sentiment_hint': 'positive'
            },
            {
                'title': f'Is {search_query} worth the price?',
                'content': f'Thinking about buying {search_query}. Has anyone here tried it? Looking for honest opinions - is it worth the investment or should I look elsewhere?',
                'platform': 'reddit',
                'engagement': {'upvotes': 156, 'downvotes': 12, 'comments': 78},
                'sentiment_hint': 'neutral'
            },
            {
                'title': f'Better alternatives to {search_query}',
                'content': f'While {search_query} is decent, I found better alternatives at this price point. Here are some options that offer better value for money.',
                'platform': 'forum',
                'engagement': {'likes': 445, 'shares': 67, 'comments': 123},
                'sentiment_hint': 'negative'
            },
            {
                'title': f'{search_query} - game changer!',
                'content': f'This {search_query} has completely changed how I work. The features are innovative and the performance is stellar. Highly recommended!',
                'platform': 'linkedin',
                'engagement': {'likes': 789, 'comments': 234, 'shares': 145},
                'sentiment_hint': 'very_positive'
            },
            {
                'title': f'My honest {search_query} review after 6 months',
                'content': f'After using {search_query} for 6 months, here\'s my honest take: it\'s solid but not perfect. Good points: reliable, good design. Bad points: expensive, limited features.',
                'platform': 'blog',
                'engagement': {'views': 2340, 'likes': 234, 'comments': 67},
                'sentiment_hint': 'mixed'
            },
            {
                'title': f'PSA: {search_query} issues to watch out for',
                'content': f'Heads up everyone - there are some known issues with {search_query} that you should be aware of before purchasing. Not trying to hate, just sharing facts.',
                'platform': 'reddit',
                'engagement': {'upvotes': 567, 'downvotes': 89, 'comments': 234},
                'sentiment_hint': 'negative'
            }
        ]
        
        # Generate varied content based on templates
        import random
        selected_templates = random.sample(social_templates, min(len(social_templates), max_results))
        
        for i, template in enumerate(selected_templates):
            result = {
                'title': template['title'],
                'url': f'https://{template["platform"]}-example.com/post/{i+1}',
                'source': template['platform'],
                'content': template['content'],
                'engagement': template['engagement']
            }
            social_results.append(result)
        
        print(f"Generated {len(social_results)} simulated social media posts")
        return social_results
        
    except Exception as e:
        print(f"Error generating social content: {str(e)}")
        return []

def extract_content_and_engagement(search_results):
    """Extract text content and engagement metrics from search results."""
    try:
        content_data = []
        
        for result in search_results:
            content_item = {
                'id': str(uuid.uuid4()),
                'title': result.get('title', ''),
                'content': result.get('content', ''),
                'source': result.get('source', 'unknown'),
                'url': result.get('url', ''),
                'engagement': result.get('engagement', {}),
                'text_for_analysis': f"{result.get('title', '')} {result.get('content', '')}"
            }
            content_data.append(content_item)
            
        print(f"Extracted content from {len(content_data)} items")
        return content_data
        
    except Exception as e:
        print(f"Error in extract_content_and_engagement: {str(e)}")
        return []

def analyze_sentiment_with_comprehend(content_data):
    """Use AWS Comprehend to analyze sentiment of content."""
    try:
        print(f"Analyzing sentiment for {len(content_data)} content items")
        sentiment_results = []
        
        for content_item in content_data:
            text = content_item['text_for_analysis']
            
            # Skip empty text
            if not text.strip():
                continue
                
            try:
                # AWS Comprehend sentiment analysis
                response = comprehend.detect_sentiment(
                    Text=text[:5000],  # Comprehend has a 5000 character limit
                    LanguageCode='en'
                )
                
                sentiment_result = {
                    'content_id': content_item['id'],
                    'source': content_item['source'],
                    'url': content_item['url'],
                    'sentiment': response['Sentiment'],
                    'confidence_scores': response['SentimentScore'],
                    'engagement': content_item['engagement'],
                    'text_sample': text[:200] + '...' if len(text) > 200 else text
                }
                
                sentiment_results.append(sentiment_result)
                
            except Exception as item_error:
                print(f"Error analyzing sentiment for item {content_item['id']}: {str(item_error)}")
                continue
                
        print(f"Successfully analyzed sentiment for {len(sentiment_results)} items")
        return sentiment_results
        
    except Exception as e:
        print(f"Error in analyze_sentiment_with_comprehend: {str(e)}")
        return []

def aggregate_sentiment_results(sentiment_results, product_name):
    """Aggregate sentiment analysis results into summary statistics."""
    try:
        if not sentiment_results:
            return {
                'overall_sentiment': 'NEUTRAL',
                'confidence': 0.0,
                'total_analyzed': 0,
                'sentiment_breakdown': {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0}
            }
        
        # Count sentiments
        sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'MIXED': 0}
        total_confidence = 0
        high_engagement_positive = 0
        high_engagement_negative = 0
        
        for result in sentiment_results:
            sentiment = result['sentiment']
            sentiment_counts[sentiment] += 1
            
            # Get confidence for the detected sentiment
            confidence_scores = result['confidence_scores']
            sentiment_confidence = confidence_scores.get(sentiment.title(), 0)
            total_confidence += sentiment_confidence
            
            # Track high-engagement content sentiment
            engagement = result.get('engagement', {})
            total_engagement = sum([
                engagement.get('likes', 0),
                engagement.get('shares', 0),
                engagement.get('upvotes', 0),
                engagement.get('comments', 0) * 2  # Weight comments higher
            ])
            
            if total_engagement > 100:  # High engagement threshold
                if sentiment == 'POSITIVE':
                    high_engagement_positive += 1
                elif sentiment == 'NEGATIVE':
                    high_engagement_negative += 1
        
        total_analyzed = len(sentiment_results)
        avg_confidence = total_confidence / total_analyzed if total_analyzed > 0 else 0
        
        # Determine overall sentiment
        positive_ratio = sentiment_counts['POSITIVE'] / total_analyzed
        negative_ratio = sentiment_counts['NEGATIVE'] / total_analyzed
        
        if positive_ratio > 0.6:
            overall_sentiment = 'POSITIVE'
        elif negative_ratio > 0.6:
            overall_sentiment = 'NEGATIVE'
        elif abs(positive_ratio - negative_ratio) < 0.2:
            overall_sentiment = 'MIXED'
        else:
            overall_sentiment = 'NEUTRAL'
        
        return {
            'overall_sentiment': overall_sentiment,
            'confidence': float(avg_confidence),
            'total_analyzed': total_analyzed,
            'sentiment_breakdown': sentiment_counts,
            'sentiment_percentages': {
                'positive': float(positive_ratio * 100),
                'negative': float(negative_ratio * 100),
                'neutral': float(sentiment_counts['NEUTRAL'] / total_analyzed * 100),
                'mixed': float(sentiment_counts['MIXED'] / total_analyzed * 100)
            },
            'high_engagement_sentiment': {
                'positive': high_engagement_positive,
                'negative': high_engagement_negative
            },
            'product_name': product_name
        }
        
    except Exception as e:
        print(f"Error in aggregate_sentiment_results: {str(e)}")
        return {
            'error': str(e),
            'overall_sentiment': 'NEUTRAL',
            'confidence': 0.0,
            'total_analyzed': 0
        }

def generate_action_items_with_bedrock(sentiment_data):
    """Use Bedrock to generate actionable insights from sentiment analysis."""
    try:
        print("Generating action items with Bedrock")
        
        # Prepare prompt for Bedrock
        prompt = create_action_items_prompt(sentiment_data)
        
        # Call Bedrock Claude model
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
                        'content': prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        action_items_text = response_body['content'][0]['text']
        
        print(f"Generated action items: {action_items_text[:200]}...")
        return action_items_text
        
    except Exception as e:
        print(f"Error in generate_action_items_with_bedrock: {str(e)}")
        return f"Error generating action items: {str(e)}"

def create_action_items_prompt(sentiment_data):
    """Create a prompt for Bedrock to generate action items."""
    sentiment_summary = sentiment_data.get('sentiment_summary', {})
    
    prompt = f"""
Based on the following sentiment analysis results, generate specific, actionable recommendations for improving the product and marketing strategy.

SENTIMENT ANALYSIS RESULTS:
- Product: {sentiment_summary.get('product_name', 'Unknown')}
- Overall Sentiment: {sentiment_summary.get('overall_sentiment', 'Unknown')}
- Confidence: {sentiment_summary.get('confidence', 0):.2f}
- Total Content Analyzed: {sentiment_summary.get('total_analyzed', 0)}

SENTIMENT BREAKDOWN:
- Positive: {sentiment_summary.get('sentiment_percentages', {}).get('positive', 0):.1f}%
- Negative: {sentiment_summary.get('sentiment_percentages', {}).get('negative', 0):.1f}%
- Neutral: {sentiment_summary.get('sentiment_percentages', {}).get('neutral', 0):.1f}%
- Mixed: {sentiment_summary.get('sentiment_percentages', {}).get('mixed', 0):.1f}%

HIGH ENGAGEMENT CONTENT:
- Positive high-engagement posts: {sentiment_summary.get('high_engagement_sentiment', {}).get('positive', 0)}
- Negative high-engagement posts: {sentiment_summary.get('high_engagement_sentiment', {}).get('negative', 0)}

Please provide actionable recommendations in the following categories:

1. IMMEDIATE ACTIONS (High Priority):
   - Actions that should be taken within 1-2 weeks
   - Focus on addressing urgent negative sentiment or capitalizing on positive momentum

2. SHORT-TERM STRATEGY (Medium Priority):
   - Actions for the next 1-3 months
   - Product improvements, marketing adjustments, content strategy

3. LONG-TERM PLANNING (Lower Priority):
   - Strategic initiatives for 3-12 months
   - Brand positioning, product development, market expansion

4. CONTENT & MESSAGING:
   - Specific messaging recommendations
   - Content themes to emphasize or avoid
   - Platform-specific strategies

5. PRODUCT IMPROVEMENTS:
   - Feature enhancements based on feedback
   - Quality improvements
   - User experience optimizations

For each recommendation, provide:
- Specific action to take
- Expected impact
- Resources needed
- Success metrics

Format your response as structured JSON with the categories above as keys.
"""
    
    return prompt

def structure_action_items(action_items_text, sentiment_data):
    """Parse and structure the action items from Bedrock response."""
    try:
        # Try to parse as JSON first
        try:
            structured_actions = json.loads(action_items_text)
            return structured_actions
        except json.JSONDecodeError:
            pass
        
        # If not JSON, create structured format
        sentiment_summary = sentiment_data.get('sentiment_summary', {})
        overall_sentiment = sentiment_summary.get('overall_sentiment', 'NEUTRAL')
        
        # Create basic structure based on sentiment
        if overall_sentiment == 'POSITIVE':
            priority_focus = "Capitalize on positive momentum and address any minor concerns"
        elif overall_sentiment == 'NEGATIVE':
            priority_focus = "Address negative feedback urgently and improve product perception"
        else:
            priority_focus = "Build stronger positive sentiment and differentiate from competition"
        
        structured_actions = {
            'priority_focus': priority_focus,
            'overall_sentiment': overall_sentiment,
            'high_priority': extract_high_priority_actions(action_items_text),
            'medium_priority': extract_medium_priority_actions(action_items_text),
            'low_priority': extract_low_priority_actions(action_items_text),
            'content_strategy': extract_content_recommendations(action_items_text),
            'product_improvements': extract_product_recommendations(action_items_text),
            'raw_recommendations': action_items_text
        }
        
        return structured_actions
        
    except Exception as e:
        print(f"Error in structure_action_items: {str(e)}")
        return {
            'error': str(e),
            'raw_recommendations': action_items_text,
            'structured': False
        }

# Helper functions for extracting specific action types
def extract_high_priority_actions(text):
    """Extract high priority actions from text."""
    # Simple keyword-based extraction - could be enhanced with NLP
    high_priority_keywords = ['urgent', 'immediate', 'critical', 'asap', 'high priority']
    lines = text.split('\n')
    high_priority = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in high_priority_keywords):
            high_priority.append(line.strip())
    
    return high_priority[:5]  # Limit to top 5

def extract_medium_priority_actions(text):
    """Extract medium priority actions from text."""
    medium_priority_keywords = ['short-term', 'medium', 'next month', 'improve']
    lines = text.split('\n')
    medium_priority = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in medium_priority_keywords):
            medium_priority.append(line.strip())
    
    return medium_priority[:5]

def extract_low_priority_actions(text):
    """Extract low priority actions from text."""
    low_priority_keywords = ['long-term', 'future', 'consider', 'explore', 'eventually']
    lines = text.split('\n')
    low_priority = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in low_priority_keywords):
            low_priority.append(line.strip())
    
    return low_priority[:5]

def extract_content_recommendations(text):
    """Extract content and messaging recommendations."""
    content_keywords = ['content', 'messaging', 'communication', 'social media', 'marketing']
    lines = text.split('\n')
    content_recs = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in content_keywords):
            content_recs.append(line.strip())
    
    return content_recs[:5]

def extract_product_recommendations(text):
    """Extract product improvement recommendations."""
    product_keywords = ['product', 'feature', 'quality', 'improvement', 'enhance', 'fix']
    lines = text.split('\n')
    product_recs = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in product_keywords):
            product_recs.append(line.strip())
    
    return product_recs[:5]

def extract_key_insights(sentiment_data, action_data):
    """Extract key insights from combined sentiment and action data."""
    try:
        sentiment_summary = sentiment_data.get('sentiment_summary', {})
        action_items = action_data.get('action_items', {})
        
        insights = []
        
        # Sentiment-based insights
        overall_sentiment = sentiment_summary.get('overall_sentiment')
        if overall_sentiment == 'POSITIVE':
            insights.append("Strong positive sentiment indicates good market reception")
        elif overall_sentiment == 'NEGATIVE':
            insights.append("Negative sentiment requires immediate attention and improvement")
        
        # Engagement insights
        high_engagement = sentiment_summary.get('high_engagement_sentiment', {})
        if high_engagement.get('negative', 0) > high_engagement.get('positive', 0):
            insights.append("Negative content is generating more engagement - address concerns promptly")
        
        # Action priority insights
        high_priority_count = len(action_items.get('high_priority', []))
        if high_priority_count > 3:
            insights.append(f"{high_priority_count} high-priority actions identified - focused execution needed")
        
        return insights[:5]  # Limit to top 5 insights
        
    except Exception as e:
        print(f"Error in extract_key_insights: {str(e)}")
        return ["Error extracting insights"]

# Database and utility functions
def convert_floats_to_decimals(obj):
    """Convert all float values in a nested object to Decimal for DynamoDB compatibility."""
    if isinstance(obj, list):
        return [convert_floats_to_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def save_analysis_to_dynamodb(table_name, analysis_record):
    """Save sentiment analysis to DynamoDB."""
    try:
        # Convert floats to Decimals for DynamoDB compatibility
        analysis_record = convert_floats_to_decimals(analysis_record)
        table = dynamodb.Table(table_name)
        table.put_item(Item=analysis_record)
        print(f"Saved analysis record to DynamoDB: {analysis_record['analysis_id']}")
    except Exception as e:
        print(f"Error saving to DynamoDB: {str(e)}")
        raise

def retrieve_analysis_from_dynamodb(analysis_id):
    """Retrieve analysis record from DynamoDB."""
    try:
        table_name = get_dynamodb_table_name()
        table = dynamodb.Table(table_name)
        # Use intelligence_id as the primary key for retrieval
        response = table.get_item(Key={'intelligence_id': analysis_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error retrieving from DynamoDB: {str(e)}")
        return None

def get_dynamodb_table_name():
    """Get DynamoDB table name from environment variables."""
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    if not table_name:
        raise Exception("DYNAMODB_TABLE_NAME environment variable not set")
    return table_name

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
            'actionGroup': 'sentiment-analysis',
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