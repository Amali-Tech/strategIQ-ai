# shared/cultural_intelligence_service.py
import logging
import os
from typing import Dict, List, Any

import boto3

from cultural_info_parser import parse_cultural_info_with_comprehend, parse_cultural_info


class CulturalIntelligenceService:
    """
    Centralized service for cultural intelligence across all Lokalize actions
    """

    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID')
        self.cache = {}  # Simple in-memory cache

    def get_comprehensive_cultural_context(self, target_locale: str, context_type: str = 'general') -> Dict[str, Any]:
        """
        Get comprehensive cultural context for a specific locale and use case

        Args:
            target_locale: Target locale (e.g., "Japan", "Germany")
            context_type: Type of context needed ('analysis', 'regeneration', 'translation', 'general')
        """
        cache_key = f"{target_locale}_{context_type}"

        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Get context-specific cultural information
            cultural_info = self._retrieve_cultural_info(target_locale, context_type)

            # Parse the information
            if len(cultural_info) > 100:
                parsed_context = parse_cultural_info_with_comprehend(cultural_info, target_locale)
            else:
                parsed_context = parse_cultural_info(cultural_info, target_locale)

            # Enhance with context-specific information
            enhanced_context = self._enhance_for_context_type(parsed_context, context_type, target_locale)

            # Cache the result
            self.cache[cache_key] = enhanced_context

            return enhanced_context

        except Exception as e:
            logging.error(f"Error getting cultural context for {target_locale}: {e}")
            return self._get_fallback_context(target_locale, context_type)

    def _retrieve_cultural_info(self, target_locale: str, context_type: str) -> str:
        """Retrieve cultural information from knowledge base"""

        # Context-specific queries
        queries = {
            'analysis': f"Cultural analysis guidelines, values, taboos, and sensitivity considerations for {target_locale} marketing content",
            'regeneration': f"Marketing best practices, successful campaigns, communication styles, and content adaptation strategies for {target_locale}",
            'translation': f"Language nuances, formality levels, cultural expressions, and translation considerations for {target_locale}",
            'general': f"Comprehensive cultural guide including values, communication, visual preferences, and business practices for {target_locale}"
        }

        query = queries.get(context_type, queries['general'])

        try:
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10  # Get more results for comprehensive context
                    }
                }
            )

            # Combine all retrieved content
            cultural_info = ""
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                cultural_info += content + "\n\n"

            return cultural_info

        except Exception as e:
            logging.error(f"Error retrieving from knowledge base: {e}")
            return ""

    def _enhance_for_context_type(self, base_context: Dict[str, Any], context_type: str, target_locale: str) -> Dict[
        str, Any]:
        """Enhance cultural context based on the specific use case"""

        enhanced_context = base_context.copy()

        if context_type == 'analysis':
            enhanced_context.update({
                'analysis_framework': self._get_analysis_framework(target_locale),
                'sensitivity_indicators': self._get_sensitivity_indicators(target_locale),
                'scoring_criteria': self._get_scoring_criteria(target_locale)
            })

        elif context_type == 'regeneration':
            enhanced_context.update({
                'adaptation_strategies': self._get_adaptation_strategies(target_locale),
                'content_templates': self._get_content_templates(target_locale),
                'brand_localization_tips': self._get_brand_localization_tips(target_locale)
            })

        elif context_type == 'translation':
            enhanced_context.update({
                'translation_guidelines': self._get_translation_guidelines(target_locale),
                'cultural_expressions': self._get_cultural_expressions(target_locale),
                'localization_rules': self._get_localization_rules(target_locale)
            })

        return enhanced_context

    def _get_analysis_framework(self, target_locale: str) -> Dict[str, Any]:
        """Get analysis framework for cultural assessment"""
        return {
            'evaluation_criteria': [
                'cultural_appropriateness',
                'communication_style_alignment',
                'visual_cultural_fit',
                'taboo_avoidance',
                'local_relevance'
            ],
            'scoring_weights': {
                'cultural_appropriateness': 0.3,
                'communication_style_alignment': 0.25,
                'visual_cultural_fit': 0.2,
                'taboo_avoidance': 0.15,
                'local_relevance': 0.1
            }
        }

    def _get_sensitivity_indicators(self, target_locale: str) -> List[str]:
        """Get cultural sensitivity indicators to watch for"""
        common_indicators = [
            'religious references',
            'gender roles',
            'family structures',
            'authority figures',
            'social hierarchies',
            'color symbolism',
            'number symbolism',
            'gesture implications'
        ]

        # Add locale-specific indicators
        locale_specific = {
            'japan': ['individual vs group focus', 'direct confrontation', 'loss of face'],
            'saudi arabia': ['religious sensitivity', 'gender representation', 'modesty considerations'],
            'germany': ['historical references', 'efficiency implications', 'environmental concerns'],
            'china': ['political sensitivity', 'lucky/unlucky numbers', 'face and respect'],
            'ghana': ['community focus', 'traditional values', 'respect for elders'],
            'france': ['formality levels', 'cultural pride', 'artistic expression'],
            'america': ['diversity and inclusion', 'informality', 'individualism']
        }

        specific_indicators = locale_specific.get(target_locale.lower(), [])
        return common_indicators + specific_indicators

    def _get_scoring_criteria(self, target_locale: str) -> Dict[str, str]:
        """Get scoring criteria for cultural analysis"""
        return {
            '9-10': 'Excellent cultural fit, highly appropriate and resonant',
            '7-8': 'Good cultural alignment with minor adjustments needed',
            '5-6': 'Moderate cultural fit, some adaptation required',
            '3-4': 'Poor cultural alignment, significant changes needed',
            '1-2': 'Culturally inappropriate, complete regeneration required'
        }

    def _get_adaptation_strategies(self, target_locale: str) -> List[Dict[str, str]]:
        """Get content adaptation strategies"""
        return [
            {
                'strategy': 'Communication Style Adaptation',
                'description': 'Adjust directness, formality, and tone to match local preferences'
            },
            {
                'strategy': 'Visual Cultural Integration',
                'description': 'Incorporate culturally appropriate colors, symbols, and imagery'
            },
            {
                'strategy': 'Value Alignment',
                'description': 'Align messaging with core cultural values and beliefs'
            },
            {
                'strategy': 'Local Context Integration',
                'description': 'Add relevant local references, seasons, or cultural events'
            }
        ]

    def _get_content_templates(self, target_locale: str) -> Dict[str, str]:
        """Get content templates for different types of marketing content"""
        templates = {
            'japan': {
                'headline': 'Respectful, benefit-focused, seasonal context',
                'body': 'Detailed explanation, group benefits, quality emphasis',
                'cta': 'Polite invitation, low-pressure approach'
            },
            'germany': {
                'headline': 'Clear, factual, efficiency-focused',
                'body': 'Technical details, quality proof, logical structure',
                'cta': 'Direct, action-oriented, time-specific'
            },
            'saudi arabia': {
                'headline': 'Respectful, family-oriented, traditional values',
                'body': 'Relationship-focused, community benefits, respectful tone',
                'cta': 'Invitation-based, relationship-building approach'
            },
            'ghana': {
                'headline': 'Community-focused, vibrant, value-driven',
                'body': 'Storytelling, local success stories, social proof',
                'cta': 'Inclusive, action-oriented, community benefit'
            },
            'america': {
                'headline': 'Bold, benefit-focused, direct',
                'body': 'Value proposition, emotional appeal, clear benefits',
                'cta': 'Urgent, action-oriented, clear next step'
            }
        }

        return templates.get(target_locale.lower(), {
            'headline': 'Clear, respectful, benefit-focused',
            'body': 'Detailed, professional, value-oriented',
            'cta': 'Clear, action-oriented, respectful'
        })

    def _get_translation_guidelines(self, target_locale: str) -> Dict[str, Any]:
        """Get translation-specific guidelines"""
        return {
            'formality_rules': self._get_formality_rules(target_locale),
            'cultural_adaptations': self._get_cultural_adaptations(target_locale),
            'avoid_literal_translations': self._get_avoid_literal_list(target_locale)
        }

    def _get_formality_rules(self, target_locale: str) -> Dict[str, str]:
        """Get formality rules for translation"""
        rules = {
            'japan': 'Use keigo (honorific language) for business contexts, avoid casual forms',
            'germany': 'Use Sie (formal you) in business, maintain professional tone',
            'saudi arabia': 'Use formal Arabic, include respectful greetings and closings',
            'france': 'Use vous (formal you), maintain elegant and sophisticated tone',
            'ghana': 'Use polite forms, respect titles and honorifics'
        }

        return {'rule': rules.get(target_locale.lower(), 'Maintain professional and respectful tone')}

    def _get_cultural_expressions(self, target_locale: str) -> List[Dict[str, str]]:
        """Get cultural expressions and their meanings"""
        expressions = {
            'japan': [
                {'expression': 'yoroshiku onegaishimasu', 'meaning': 'please treat me favorably',
                 'usage': 'business introductions'},
                {'expression': 'otsukaresama', 'meaning': 'thank you for your hard work',
                 'usage': 'workplace appreciation'}
            ],
            'germany': [
                {'expression': 'mit freundlichen Grüßen', 'meaning': 'with friendly greetings',
                 'usage': 'formal email closing'},
                {'expression': 'Qualität hat ihren Preis', 'meaning': 'quality has its price',
                 'usage': 'justifying premium pricing'}
            ],
            'saudi arabia': [
                {'expression': 'Inshallah', 'meaning': 'if God wills it',
                 'usage': 'expressing hope for future events'},
                {'expression': 'As-salamu alaykum', 'meaning': 'peace be upon you',
                 'usage': 'common greeting'}
            ],
            'ghana': [
                {'expression': 'Akwaaba', 'meaning': 'welcome',
                 'usage': 'greeting guests'},
                {'expression': 'Medase', 'meaning': 'thank you',
                 'usage': 'expressing gratitude'}
            ]
        }

        return expressions.get(target_locale.lower(), [])

    def _get_localization_rules(self, target_locale: str) -> List[str]:
        """Get localization rules beyond translation"""
        return [
            'Adapt date and time formats to local conventions',
            'Use local currency and pricing formats',
            'Adjust contact information and business hours',
            'Include local legal disclaimers if required',
            'Adapt imagery to show local demographics',
            'Use culturally appropriate color schemes'
        ]

    def _get_fallback_context(self, target_locale: str, context_type: str) -> Dict[str, Any]:
        """Fallback context when retrieval fails"""
        from cultural_info_parser import get_default_cultural_context
        base_context = get_default_cultural_context(target_locale)

        # Add minimal context-specific enhancements
        if context_type == 'analysis':
            base_context['analysis_framework'] = {'evaluation_criteria': ['appropriateness', 'relevance']}
        elif context_type == 'regeneration':
            base_context['adaptation_strategies'] = [
                {'strategy': 'Basic Adaptation', 'description': 'Adjust tone and style'}]
        elif context_type == 'translation':
            base_context['translation_guidelines'] = {'formality_rules': {'rule': 'Maintain professional tone'}}

        return base_context


# Singleton instance
cultural_service = CulturalIntelligenceService()
