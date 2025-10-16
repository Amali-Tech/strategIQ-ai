import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda handler for Voice of the Market Agent - Sentiment Analysis action group
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters from Bedrock agent event format
        parameters = {}
        
        # Bedrock agents pass parameters in different formats - handle all cases
        if 'parameters' in event:
            parameters = event['parameters']
            logger.info(f"Found parameters in event['parameters']: {parameters}")
        elif 'inputText' in event:
            parameters = {'inputText': event['inputText']}
            logger.info(f"Found inputText in event: {event['inputText']}")
        elif 'requestBody' in event:
            if 'content' in event['requestBody']:
                for content_type, content_data in event['requestBody']['content'].items():
                    if 'properties' in content_data:
                        parameters = content_data['properties']
                        logger.info(f"Found parameters in requestBody content: {parameters}")
                        break
        elif 'apiPath' in event and 'httpMethod' in event:
            # API Gateway format
            if event.get('body'):
                try:
                    parameters = json.loads(event['body'])
                    logger.info(f"Parsed parameters from body: {parameters}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse body as JSON: {event['body']}")
        
        # Log what we extracted
        logger.info(f"Final extracted parameters: {parameters}")
        
        # Extract specific parameters with defaults
        brand_keywords = parameters.get('brand_keywords', parameters.get('keywords', ['sample_brand']))
        time_range = parameters.get('time_range', '30d')
        channels = parameters.get('channels', ['social_media', 'news_media'])
        
        logger.info(f"Processing sentiment analysis - Keywords: {brand_keywords}, Range: {time_range}, Channels: {channels}")
        
        # Placeholder response structure
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "sentiment_analysis",
                "function": "analyze_market_sentiment",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "success",
                                "sentiment_analysis": {
                                    "overall_sentiment": {
                                        "score": 0.72,
                                        "classification": "positive",
                                        "confidence": 0.89,
                                        "trend": "improving"
                                    },
                                    "sentiment_breakdown": {
                                        "positive": 0.65,
                                        "neutral": 0.25,
                                        "negative": 0.10
                                    },
                                    "source_analysis": {
                                        "social_media": {
                                            "platforms": {
                                                "twitter": {
                                                    "sentiment_score": 0.68,
                                                    "volume": 1250,
                                                    "engagement_rate": 0.045,
                                                    "key_topics": ["innovation", "user_experience", "pricing"]
                                                },
                                                "linkedin": {
                                                    "sentiment_score": 0.78,
                                                    "volume": 340,
                                                    "engagement_rate": 0.082,
                                                    "key_topics": ["business_value", "roi", "integration"]
                                                },
                                                "reddit": {
                                                    "sentiment_score": 0.62,
                                                    "volume": 89,
                                                    "engagement_rate": 0.156,
                                                    "key_topics": ["technical_issues", "support", "features"]
                                                }
                                            }
                                        },
                                        "news_media": {
                                            "sentiment_score": 0.81,
                                            "article_count": 45,
                                            "reach_estimate": 2500000,
                                            "key_themes": ["market_leadership", "innovation", "growth"]
                                        },
                                        "review_sites": {
                                            "sentiment_score": 0.74,
                                            "review_count": 1890,
                                            "average_rating": 4.2,
                                            "common_praise": ["ease_of_use", "customer_support", "reliability"],
                                            "common_complaints": ["pricing", "learning_curve", "limited_features"]
                                        }
                                    },
                                    "temporal_analysis": {
                                        "last_7_days": {
                                            "sentiment_score": 0.75,
                                            "volume_change": "+12%",
                                            "key_events": ["product_launch", "positive_review"]
                                        },
                                        "last_30_days": {
                                            "sentiment_score": 0.71,
                                            "volume_change": "+8%",
                                            "key_events": ["conference_presentation", "partnership_announcement"]
                                        },
                                        "last_90_days": {
                                            "sentiment_score": 0.69,
                                            "volume_change": "+15%",
                                            "key_events": ["funding_round", "expansion_news"]
                                        }
                                    },
                                    "demographic_insights": {
                                        "age_groups": {
                                            "18-24": {"sentiment": 0.68, "volume_share": 0.15},
                                            "25-34": {"sentiment": 0.74, "volume_share": 0.35},
                                            "35-44": {"sentiment": 0.76, "volume_share": 0.30},
                                            "45+": {"sentiment": 0.71, "volume_share": 0.20}
                                        },
                                        "geographic_distribution": {
                                            "north_america": {"sentiment": 0.75, "volume_share": 0.45},
                                            "europe": {"sentiment": 0.72, "volume_share": 0.30},
                                            "asia_pacific": {"sentiment": 0.69, "volume_share": 0.20},
                                            "other": {"sentiment": 0.66, "volume_share": 0.05}
                                        }
                                    },
                                    "competitive_sentiment": {
                                        "vs_competitor_a": {
                                            "relative_sentiment": "+0.08",
                                            "share_of_voice": "higher",
                                            "key_differentiators": ["customer_service", "innovation"]
                                        },
                                        "vs_competitor_b": {
                                            "relative_sentiment": "+0.03",
                                            "share_of_voice": "similar",
                                            "key_differentiators": ["pricing", "features"]
                                        }
                                    },
                                    "actionable_insights": [
                                        "Leverage positive customer service sentiment in marketing",
                                        "Address pricing concerns in value proposition",
                                        "Amplify innovation messaging on LinkedIn",
                                        "Monitor technical issue discussions on Reddit"
                                    ],
                                    "risk_indicators": [
                                        {
                                            "type": "pricing_sensitivity",
                                            "severity": "medium",
                                            "trend": "stable",
                                            "recommendation": "Develop value-focused messaging"
                                        }
                                    ]
                                }
                            })
                        }
                    }
                }
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Full event for debugging: {json.dumps(event, default=str)}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "sentiment_analysis",
                "function": "analyze_market_sentiment",
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "status": "error",
                                "message": f"Failed to analyze market sentiment: {str(e)}",
                                "debug_info": {
                                    "event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict",
                                    "context_info": str(context)
                                }
                            })
                        }
                    }
                }
            }
        }