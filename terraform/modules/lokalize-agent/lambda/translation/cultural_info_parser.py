import logging
import re
from typing import Dict, List, Any

import boto3


def parse_cultural_info(cultural_info: str, target_locale: str) -> Dict[str, Any]:
    """
    Parse cultural information from knowledge base content into structured data

    Args:
        cultural_info: Raw text from knowledge base retrieval
        target_locale: Target locale/country (e.g., "Japan", "Germany", "Saudi Arabia")

    Returns:
        Structured cultural information dictionary
    """
    try:
        # Initialize the parser
        parser = CulturalInfoParser(target_locale)

        # Parse the cultural information
        structured_data = parser.parse(cultural_info)

        return structured_data

    except Exception as e:
        logging.error(f"Error parsing cultural info for {target_locale}: {e}")
        return get_default_cultural_context(target_locale)


class CulturalInfoParser:
    """Advanced parser for extracting structured cultural information"""

    def __init__(self, target_locale: str):
        self.target_locale = target_locale.lower()
        self.comprehend = None  # Initialize if needed

        # Cultural categories and their keywords
        self.cultural_patterns = {
            'values': {
                'keywords': [
                    'values', 'beliefs', 'principles', 'ideals', 'ethics', 'morals',
                    'important', 'priority', 'cherish', 'respect', 'honor'
                ],
                'patterns': [
                    r'(?:cultural?\s+)?values?\s*(?:include|are|:)\s*([^.!?]+)',
                    r'(?:they\s+)?(?:value|prize|cherish|respect)\s+([^.!?]+)',
                    r'important\s+(?:cultural?\s+)?(?:aspects?|values?|beliefs?)\s*(?:include|are|:)\s*([^.!?]+)'
                ]
            },
            'communication_style': {
                'keywords': [
                    'communication', 'speaking', 'talking', 'conversation', 'dialogue',
                    'direct', 'indirect', 'formal', 'informal', 'polite', 'casual',
                    'tone', 'manner', 'style', 'approach'
                ],
                'patterns': [
                    r'communication\s+(?:style|approach|manner)\s*(?:is|tends?\s+to\s+be|:)\s*([^.!?]+)',
                    r'(?:they\s+)?(?:speak|communicate|talk)\s+(?:in\s+a\s+)?([^.!?]*(?:direct|indirect|formal|informal|polite|casual)[^.!?]*)',
                    r'(?:conversation|dialogue)\s+(?:style|approach|is)\s*([^.!?]+)'
                ]
            },
            'visual_preferences': {
                'keywords': [
                    'visual', 'design', 'aesthetic', 'appearance', 'look', 'style',
                    'color', 'imagery', 'graphics', 'layout', 'presentation',
                    'clean', 'minimalist', 'bold', 'bright', 'traditional'
                ],
                'patterns': [
                    r'visual\s+(?:preferences?|style|aesthetic)\s*(?:include|are|:)\s*([^.!?]+)',
                    r'(?:design|aesthetic)\s+(?:preferences?|style|approach)\s*(?:is|are|:)\s*([^.!?]+)',
                    r'(?:prefer|like|favor)\s+([^.!?]*(?:visual|design|aesthetic|color|imagery)[^.!?]*)'
                ]
            },
            'taboos': {
                'keywords': [
                    'taboo', 'avoid', 'forbidden', 'inappropriate', 'offensive',
                    'sensitive', 'controversial', 'unacceptable', 'prohibited',
                    'don\'t', 'never', 'shouldn\'t', 'not recommended'
                ],
                'patterns': [
                    r'(?:cultural?\s+)?taboos?\s*(?:include|are|:)\s*([^.!?]+)',
                    r'(?:should\s+)?avoid\s+([^.!?]+)',
                    r'(?:is|are)\s+(?:considered\s+)?(?:inappropriate|offensive|taboo|forbidden)\s*:?\s*([^.!?]+)',
                    r'(?:don\'t|never|shouldn\'t)\s+([^.!?]+)'
                ]
            },
            'business_practices': {
                'keywords': [
                    'business', 'work', 'professional', 'corporate', 'meeting',
                    'negotiation', 'relationship', 'hierarchy', 'authority'
                ],
                'patterns': [
                    r'business\s+(?:practices?|culture|etiquette)\s*(?:include|are|:)\s*([^.!?]+)',
                    r'(?:in\s+)?(?:professional|business)\s+(?:settings?|contexts?)\s*([^.!?]+)',
                    r'(?:work|professional)\s+(?:culture|environment|relationships?)\s*([^.!?]+)'
                ]
            },
            'seasonal_considerations': {
                'keywords': [
                    'season', 'holiday', 'festival', 'celebration', 'tradition',
                    'spring', 'summer', 'autumn', 'winter', 'new year', 'christmas'
                ],
                'patterns': [
                    r'(?:seasonal|holiday)\s+(?:considerations?|traditions?|celebrations?)\s*(?:include|are|:)\s*([^.!?]+)',
                    r'(?:during|in)\s+([^.!?]*(?:season|holiday|festival|celebration)[^.!?]*)',
                    r'(?:traditional|cultural)\s+(?:holidays?|festivals?|celebrations?)\s*([^.!?]+)'
                ]
            }
        }

        # Locale-specific enhancements
        self.locale_specific_patterns = self._get_locale_specific_patterns()

    def parse(self, cultural_info: str) -> Dict[str, Any]:
        """Main parsing method"""
        if not cultural_info or not cultural_info.strip():
            return get_default_cultural_context(self.target_locale)

        # Clean and preprocess text
        cleaned_text = self._preprocess_text(cultural_info)

        # Extract structured information
        structured_data = {
            'values': self._extract_values(cleaned_text),
            'communication_style': self._extract_communication_style(cleaned_text),
            'visual_preferences': self._extract_visual_preferences(cleaned_text),
            'taboos': self._extract_taboos(cleaned_text),
            'business_practices': self._extract_business_practices(cleaned_text),
            'seasonal_considerations': self._extract_seasonal_considerations(cleaned_text),
            'successful_campaigns': self._extract_successful_campaigns(cleaned_text),
            'local_trends': self._extract_local_trends(cleaned_text),
            'language_nuances': self._extract_language_nuances(cleaned_text)
        }

        # Apply locale-specific enhancements
        structured_data = self._apply_locale_enhancements(structured_data)

        # Validate and clean results
        structured_data = self._validate_and_clean(structured_data)

        return structured_data

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess the input text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common document artifacts
        text = re.sub(r'(?:page\s+\d+|source:|reference:|note:)', '', text, flags=re.IGNORECASE)

        # Split into sentences for better processing
        sentences = re.split(r'[.!?]+', text)

        return ' '.join(sentence.strip() for sentence in sentences if sentence.strip())

    def _extract_values(self, text: str) -> List[str]:
        """Extract cultural values"""
        values = set()

        # Use patterns to extract values
        for pattern in self.cultural_patterns['values']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                extracted = match.group(1).strip()
                values.update(self._parse_list_items(extracted))

        # Look for keyword-based values
        value_keywords = [
            'respect', 'honor', 'tradition', 'family', 'community', 'harmony',
            'hierarchy', 'authority', 'individualism', 'collectivism', 'punctuality',
            'efficiency', 'quality', 'craftsmanship', 'innovation', 'stability',
            'loyalty', 'trust', 'honesty', 'integrity', 'humility', 'pride'
        ]

        for keyword in value_keywords:
            if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
                values.add(keyword)

        return list(values)[:10]  # Limit to top 10

    def _extract_communication_style(self, text: str) -> str:
        """Extract communication style description"""
        styles = []

        # Pattern-based extraction
        for pattern in self.cultural_patterns['communication_style']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                styles.append(match.group(1).strip())

        # Keyword-based detection
        style_indicators = {
            'direct': ['direct', 'straightforward', 'blunt', 'frank'],
            'indirect': ['indirect', 'subtle', 'implied', 'diplomatic'],
            'formal': ['formal', 'respectful', 'ceremonial', 'structured'],
            'informal': ['informal', 'casual', 'relaxed', 'friendly'],
            'high-context': ['context', 'implicit', 'nonverbal', 'reading between lines'],
            'low-context': ['explicit', 'clear', 'specific', 'detailed']
        }

        detected_styles = []
        for style, indicators in style_indicators.items():
            if any(re.search(rf'\b{indicator}\b', text, re.IGNORECASE) for indicator in indicators):
                detected_styles.append(style)

        if styles:
            return '; '.join(styles[:2])  # Top 2 descriptions
        elif detected_styles:
            return ', '.join(detected_styles)
        else:
            return "professional and respectful"

    def _extract_visual_preferences(self, text: str) -> str:
        """Extract visual and design preferences"""
        preferences = []

        # Pattern-based extraction
        for pattern in self.cultural_patterns['visual_preferences']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                preferences.append(match.group(1).strip())

        # Color and design keywords
        visual_keywords = {
            'colors': ['red', 'blue', 'green', 'gold', 'white', 'black', 'bright', 'muted', 'vibrant'],
            'styles': ['minimalist', 'clean', 'bold', 'traditional', 'modern', 'elegant', 'simple', 'complex'],
            'elements': ['imagery', 'symbols', 'patterns', 'typography', 'layout']
        }

        detected_preferences = []
        for category, keywords in visual_keywords.items():
            found = [kw for kw in keywords if re.search(rf'\b{kw}\b', text, re.IGNORECASE)]
            if found:
                detected_preferences.extend(found[:3])  # Top 3 per category

        if preferences:
            return '; '.join(preferences[:2])
        elif detected_preferences:
            return ', '.join(detected_preferences)
        else:
            return "clean and professional design"

    def _extract_taboos(self, text: str) -> List[str]:
        """Extract cultural taboos and things to avoid"""
        taboos = set()

        # Pattern-based extraction
        for pattern in self.cultural_patterns['taboos']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                extracted = match.group(1).strip()
                taboos.update(self._parse_list_items(extracted))

        # Common taboo keywords
        taboo_keywords = [
            'aggressive sales', 'pushy', 'confrontational', 'disrespectful',
            'inappropriate imagery', 'offensive content', 'stereotypes',
            'religious sensitivity', 'political references', 'controversial topics'
        ]

        for keyword in taboo_keywords:
            if re.search(rf'{keyword}', text, re.IGNORECASE):
                taboos.add(keyword)

        return list(taboos)[:8]  # Limit to top 8

    def _extract_business_practices(self, text: str) -> List[str]:
        """Extract business and professional practices"""
        practices = set()

        for pattern in self.cultural_patterns['business_practices']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                extracted = match.group(1).strip()
                practices.update(self._parse_list_items(extracted))

        return list(practices)[:6]

    def _extract_seasonal_considerations(self, text: str) -> List[str]:
        """Extract seasonal and holiday considerations"""
        considerations = set()

        for pattern in self.cultural_patterns['seasonal_considerations']['patterns']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                extracted = match.group(1).strip()
                considerations.update(self._parse_list_items(extracted))

        return list(considerations)[:5]

    def _extract_successful_campaigns(self, text: str) -> List[str]:
        """Extract information about successful marketing campaigns"""
        campaigns = []

        campaign_patterns = [
            r'successful\s+campaigns?\s*(?:include|are|:)\s*([^.!?]+)',
            r'(?:effective|popular)\s+(?:marketing|advertising)\s*([^.!?]+)',
            r'(?:brands?|companies?)\s+(?:that\s+)?(?:succeeded|worked|resonated)\s*([^.!?]+)'
        ]

        for pattern in campaign_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                campaigns.append(match.group(1).strip())

        return campaigns[:4]

    def _extract_local_trends(self, text: str) -> List[str]:
        """Extract local market trends"""
        trends = []

        trend_patterns = [
            r'(?:current|recent|popular)\s+trends?\s*(?:include|are|:)\s*([^.!?]+)',
            r'trending\s+(?:topics?|themes?|styles?)\s*([^.!?]+)',
            r'(?:consumers?|customers?)\s+(?:prefer|like|want)\s*([^.!?]+)'
        ]

        for pattern in trend_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                trends.append(match.group(1).strip())

        return trends[:4]

    def _extract_language_nuances(self, text: str) -> Dict[str, Any]:
        """Extract language-specific nuances"""
        nuances = {
            'formality_level': 'medium',
            'preferred_pronouns': [],
            'honorifics': [],
            'tone_preferences': []
        }

        # Detect formality level
        if re.search(r'formal|respectful|ceremonial|structured', text, re.IGNORECASE):
            nuances['formality_level'] = 'high'
        elif re.search(r'informal|casual|relaxed|friendly', text, re.IGNORECASE):
            nuances['formality_level'] = 'low'

        # Extract tone preferences
        tone_keywords = ['polite', 'respectful', 'warm', 'professional', 'friendly', 'authoritative']
        nuances['tone_preferences'] = [
            tone for tone in tone_keywords
            if re.search(rf'\b{tone}\b', text, re.IGNORECASE)
        ]

        return nuances

    def _parse_list_items(self, text: str) -> List[str]:
        """Parse comma-separated or bullet-pointed lists"""
        if not text:
            return []

        # Split by common delimiters
        items = re.split(r'[,;]\s*|(?:\s+and\s+)|(?:\s*\|\s*)', text)

        # Clean and filter items
        cleaned_items = []
        for item in items:
            item = item.strip().strip('•-*').strip()
            if item and len(item) > 2 and len(item) < 100:  # Reasonable length
                cleaned_items.append(item)

        return cleaned_items

    def _get_locale_specific_patterns(self) -> Dict[str, Any]:
        """Get locale-specific parsing patterns"""
        locale_patterns = {
            'japan': {
                'values': ['wa (harmony)', 'respect', 'group consensus', 'face-saving', 'hierarchy'],
                'communication': 'indirect, polite, high-context',
                'visual': 'clean, minimalist, seasonal elements, subtle colors',
                'taboos': ['direct confrontation', 'individual focus over group', 'overly casual tone']
            },
            'germany': {
                'values': ['efficiency', 'punctuality', 'quality', 'precision', 'directness'],
                'communication': 'direct, factual, professional, structured',
                'visual': 'clean, technical, detailed information, professional',
                'taboos': ['exaggerated claims', 'overly emotional appeals', 'unprofessional presentation']
            },
            'saudi arabia': {
                'values': ['respect', 'tradition', 'family', 'hospitality', 'religious values'],
                'communication': 'respectful, formal, relationship-focused',
                'visual': 'elegant, traditional elements, appropriate imagery',
                'taboos': ['inappropriate imagery', 'religious insensitivity', 'cultural stereotypes']
            },
            'china': {
                'values': ['harmony', 'respect for authority', 'face', 'relationships', 'tradition'],
                'communication': 'indirect, respectful, relationship-building',
                'visual': 'red and gold colors, traditional symbols, prosperity themes',
                'taboos': ['loss of face', 'political sensitivity', 'unlucky numbers (4)']
            },
            'ghana': {
                'values': ['community', 'respect for elders', 'family', 'tradition', 'hospitality'],
                'communication': 'respectful, indirect, storytelling',
                'visual': 'bright colors, traditional patterns, cultural symbols',
                'taboos': ['disrespecting elders', 'public criticism', 'sensitive political topics']
            },
            'america': {
                'values': ['individualism', 'freedom', 'innovation', 'equality', 'diversity'],
                'communication': 'direct, informal, assertive',
                'visual': 'bold colors, modern design, diverse representation',
                'taboos': ['discrimination', 'stereotyping', 'political correctness']
            }
        }

        return locale_patterns.get(self.target_locale, {})

    def _apply_locale_enhancements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply locale-specific enhancements to parsed data"""
        locale_data = self.locale_specific_patterns

        if not locale_data:
            return data

        # Enhance with locale-specific defaults if data is sparse
        if len(data['values']) < 3 and 'values' in locale_data:
            data['values'].extend(locale_data['values'][:5])
            data['values'] = list(set(data['values']))  # Remove duplicates

        if not data['communication_style'] and 'communication' in locale_data:
            data['communication_style'] = locale_data['communication']

        if not data['visual_preferences'] and 'visual' in locale_data:
            data['visual_preferences'] = locale_data['visual']

        if len(data['taboos']) < 2 and 'taboos' in locale_data:
            data['taboos'].extend(locale_data['taboos'])
            data['taboos'] = list(set(data['taboos']))

        return data

    def _validate_and_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the extracted data"""
        # Ensure minimum data quality
        if not data['values']:
            data['values'] = ['respect', 'quality', 'professionalism']

        if not data['communication_style']:
            data['communication_style'] = 'professional and respectful'

        if not data['visual_preferences']:
            data['visual_preferences'] = 'clean and professional design'

        if not data['taboos']:
            data['taboos'] = ['inappropriate content', 'cultural insensitivity']

        # Remove duplicates and limit lengths
        for key in ['values', 'taboos', 'business_practices', 'seasonal_considerations']:
            if isinstance(data[key], list):
                data[key] = list(set(data[key]))[:8]  # Max 8 items

        return data


def get_default_cultural_context(target_locale: str) -> Dict[str, Any]:
    """Fallback cultural context if parsing fails"""
    defaults = {
        'japan': {
            'values': ['respect', 'harmony', 'quality', 'tradition', 'group consensus'],
            'communication_style': 'indirect, polite, formal, high-context',
            'visual_preferences': 'clean, minimalist, seasonal elements, subtle colors',
            'taboos': ['direct confrontation', 'overly casual tone', 'individual focus over group'],
            'business_practices': ['relationship building', 'consensus decision making', 'formal meetings'],
            'seasonal_considerations': ['cherry blossom season', 'new year traditions', 'seasonal greetings'],
            'successful_campaigns': [],
            'local_trends': [],
            'language_nuances': {'formality_level': 'high', 'tone_preferences': ['polite', 'respectful']}
        },
        'germany': {
            'values': ['efficiency', 'quality', 'precision', 'reliability', 'punctuality'],
            'communication_style': 'direct, factual, professional, structured',
            'visual_preferences': 'clean, structured, technical details, professional',
            'taboos': ['exaggerated claims', 'overly emotional appeals', 'unprofessional presentation'],
            'business_practices': ['punctuality', 'detailed planning', 'quality focus'],
            'seasonal_considerations': ['Christmas markets', 'Oktoberfest', 'summer holidays'],
            'successful_campaigns': [],
            'local_trends': [],
            'language_nuances': {'formality_level': 'medium', 'tone_preferences': ['professional', 'direct']}
        },
        'saudi arabia': {
            'values': ['respect', 'tradition', 'family', 'hospitality', 'religious values'],
            'communication_style': 'respectful, formal, relationship-focused',
            'visual_preferences': 'elegant, traditional elements, appropriate imagery',
            'taboos': ['inappropriate imagery', 'religious insensitivity', 'cultural stereotypes'],
            'business_practices': ['relationship building', 'respect for hierarchy', 'formal protocols'],
            'seasonal_considerations': ['Ramadan', 'Eid celebrations', 'Hajj season'],
            'successful_campaigns': [],
            'local_trends': [],
            'language_nuances': {'formality_level': 'high', 'tone_preferences': ['respectful', 'formal']}
        },
        'ghana': {
            'values': ['community', 'respect for elders', 'family', 'tradition', 'hospitality'],
            'communication_style': 'respectful, indirect, storytelling',
            'visual_preferences': 'bright colors, traditional patterns, cultural symbols',
            'taboos': ['disrespecting elders', 'public criticism', 'sensitive political topics'],
            'business_practices': ['relationship building', 'respect for hierarchy', 'community focus'],
            'seasonal_considerations': ['festivals', 'harvest celebrations', 'traditional holidays'],
            'successful_campaigns': [],
            'local_trends': [],
            'language_nuances': {'formality_level': 'medium', 'tone_preferences': ['respectful', 'warm']}
        },
    }

    locale_key = target_locale.lower()
    return defaults.get(locale_key, {
        'values': ['respect', 'quality', 'professionalism'],
        'communication_style': 'professional and respectful',
        'visual_preferences': 'clean and professional design',
        'taboos': ['inappropriate content', 'cultural insensitivity'],
        'business_practices': ['professional conduct', 'quality focus'],
        'seasonal_considerations': ['local holidays', 'seasonal preferences'],
        'successful_campaigns': [],
        'local_trends': [],
        'language_nuances': {'formality_level': 'medium', 'tone_preferences': ['professional']}
    })


# Optional: Enhanced version using Amazon Comprehend for better extraction
def parse_cultural_info_with_comprehend(cultural_info: str, target_locale: str) -> Dict[str, Any]:
    """
    Enhanced version using Amazon Comprehend for better NLP extraction
    """
    try:
        comprehend = boto3.client('comprehend')

        # Detect key phrases
        key_phrases_response = comprehend.detect_key_phrases(
            Text=cultural_info[:5000],  # Comprehend limit
            LanguageCode='en'
        )

        # Detect entities
        entities_response = comprehend.detect_entities(
            Text=cultural_info[:5000],
            LanguageCode='en'
        )

        # Use the enhanced data for better parsing
        parser = CulturalInfoParser(target_locale)
        structured_data = parser.parse(cultural_info)

        # Enhance with Comprehend results
        key_phrases = [phrase['Text'] for phrase in key_phrases_response['KeyPhrases']]
        entities = [entity['Text'] for entity in entities_response['Entities']]

        # Add relevant phrases to appropriate categories
        for phrase in key_phrases:
            if any(word in phrase.lower() for word in ['value', 'important', 'belief']):
                structured_data['values'].append(phrase)
            elif any(word in phrase.lower() for word in ['avoid', 'taboo', 'inappropriate']):
                structured_data['taboos'].append(phrase)

        # Clean up duplicates
        structured_data['values'] = list(set(structured_data['values']))[:10]
        structured_data['taboos'] = list(set(structured_data['taboos']))[:8]

        return structured_data

    except Exception as e:
        logging.error(f"Error using Comprehend for parsing: {e}")
        return parse_cultural_info(cultural_info, target_locale)
