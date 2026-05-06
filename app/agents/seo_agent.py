"""
SEO Agent - Advanced Keyword Research & Content Optimization
Analyzes content, finds low-competition keywords, and auto-optimizes blogs
with real content analysis and scoring.

Features:
- Real keyword data from Google Trends (PyTrends)
- Actual content analysis (not AI self-reporting)
- Readability scoring (Flesch-Kincaid)
- Keyword density analysis
- Heading structure validation
- Meta description optimization
- Content length recommendations
- Internal/external link detection
- Response caching for keyword lookups
"""

import google.generativeai as genai
import requests
import os
import re
import math
from typing import Dict, List, Optional
from collections import Counter
from app.utils.cache import cache


class SEOAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

        # RapidAPI Key for SEO APIs
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY', '')

        # SEO Keyword Research API on RapidAPI
        self.seo_api = {
            "host": "seo-keyword-research.p.rapidapi.com",
            "base_url": "https://seo-keyword-research.p.rapidapi.com"
        }

        # SEO Checker API on RapidAPI (URL analysis)
        self.seo_checker_api = {
            "host": "seo-checker2.p.rapidapi.com",
            "base_url": "https://seo-checker2.p.rapidapi.com"
        }

        # Use PyTrends as backup data source
        self.use_pytrends = True

        # SEO Best Practices Constants
        self.IDEAL_TITLE_LENGTH = (50, 60)
        self.IDEAL_META_LENGTH = (150, 160)
        self.IDEAL_KEYWORD_DENSITY = (1.0, 2.5)  # percentage
        self.MIN_CONTENT_WORDS = 300
        self.IDEAL_CONTENT_WORDS = (1000, 2000)
        self.IDEAL_PARAGRAPH_LENGTH = (100, 200)  # words
        self.IDEAL_SENTENCE_LENGTH = (15, 20)  # words

    # =========================================
    # ADVANCED CONTENT ANALYSIS
    # =========================================
    def analyze_content(self, content: str, title: str = "", target_keyword: str = "") -> Dict:
        """
        Comprehensive SEO analysis of content
        Returns detailed metrics and scores
        """
        # Clean content for analysis
        text_only = self._strip_markdown(content)
        words = text_only.lower().split()
        word_count = len(words)

        # Basic metrics
        sentences = self._count_sentences(text_only)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]

        # Heading analysis
        headings = self._analyze_headings(content)

        # Keyword analysis
        keyword_analysis = self._analyze_keyword_usage(content, text_only, target_keyword) if target_keyword else {}

        # Readability
        readability = self._calculate_readability(text_only, sentences, word_count)

        # Link analysis
        links = self._analyze_links(content)

        # Image analysis
        images = self._analyze_images(content)

        # Title analysis
        title_analysis = self._analyze_title(title, target_keyword) if title else {}

        # Calculate overall SEO score
        seo_score = self._calculate_comprehensive_seo_score(
            word_count=word_count,
            headings=headings,
            keyword_analysis=keyword_analysis,
            readability=readability,
            links=links,
            images=images,
            title_analysis=title_analysis
        )

        return {
            "word_count": word_count,
            "sentence_count": sentences,
            "paragraph_count": len(paragraphs),
            "avg_sentence_length": round(word_count / max(sentences, 1), 1),
            "avg_paragraph_length": round(word_count / max(len(paragraphs), 1), 1),
            "headings": headings,
            "keyword_analysis": keyword_analysis,
            "readability": readability,
            "links": links,
            "images": images,
            "title_analysis": title_analysis,
            "seo_score": seo_score,
            "issues": self._identify_issues(seo_score)
        }

    def _strip_markdown(self, content: str) -> str:
        """Remove markdown formatting to get plain text"""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', content)
        text = re.sub(r'`[^`]+`', '', text)
        # Remove images
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove headers markers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # Remove list markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        return text.strip()

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    def _analyze_headings(self, content: str) -> Dict:
        """Analyze heading structure"""
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        headings = []

        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({"level": level, "text": text})

        # Check hierarchy
        levels_used = [h['level'] for h in headings]
        has_h1 = 1 in levels_used
        has_h2 = 2 in levels_used
        proper_hierarchy = self._check_heading_hierarchy(levels_used)

        # Count by level
        level_counts = Counter(levels_used)

        return {
            "total": len(headings),
            "has_h1": has_h1,
            "has_h2": has_h2,
            "h1_count": level_counts.get(1, 0),
            "h2_count": level_counts.get(2, 0),
            "h3_count": level_counts.get(3, 0),
            "proper_hierarchy": proper_hierarchy,
            "headings_list": headings,
            "score": self._score_headings(headings, has_h1, has_h2, proper_hierarchy)
        }

    def _check_heading_hierarchy(self, levels: List[int]) -> bool:
        """Check if headings follow proper hierarchy (no skipping levels)"""
        if not levels:
            return True

        for i in range(1, len(levels)):
            # Allow going up any amount, but down only by 1
            if levels[i] > levels[i-1] + 1:
                return False
        return True

    def _score_headings(self, headings: List, has_h1: bool, has_h2: bool, proper_hierarchy: bool) -> int:
        """Score heading structure out of 100"""
        score = 0

        if headings:
            score += 20  # Has headings
        if has_h1:
            score += 25  # Has H1
        if has_h2:
            score += 25  # Has H2
        if proper_hierarchy:
            score += 20  # Proper hierarchy
        if len(headings) >= 3:
            score += 10  # Multiple headings for structure

        return min(100, score)

    def _analyze_keyword_usage(self, content: str, text_only: str, keyword: str) -> Dict:
        """Analyze how a keyword is used in content"""
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        text_lower = text_only.lower()

        # Count occurrences
        keyword_count = text_lower.count(keyword_lower)
        word_count = len(text_lower.split())

        # Calculate density
        keyword_words = len(keyword_lower.split())
        density = (keyword_count * keyword_words / max(word_count, 1)) * 100

        # Check positions
        in_title = keyword_lower in content_lower[:200]  # First 200 chars likely has title

        # Check first paragraph (first 500 chars of text)
        first_para = text_lower[:500]
        in_first_paragraph = keyword_lower in first_para

        # Check in headings
        heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        headings_text = ' '.join(m.group(1).lower() for m in heading_pattern.finditer(content))
        in_headings = keyword_lower in headings_text

        # Check variations
        keyword_parts = keyword_lower.split()
        partial_matches = sum(1 for part in keyword_parts if part in text_lower)

        # Score keyword usage
        score = self._score_keyword_usage(
            keyword_count, density, in_title, in_first_paragraph, in_headings, word_count
        )

        return {
            "keyword": keyword,
            "count": keyword_count,
            "density": round(density, 2),
            "density_status": self._get_density_status(density),
            "in_title": in_title,
            "in_first_paragraph": in_first_paragraph,
            "in_headings": in_headings,
            "partial_matches": partial_matches,
            "score": score
        }

    def _get_density_status(self, density: float) -> str:
        """Get status of keyword density"""
        if density < 0.5:
            return "too_low"
        elif density < 1.0:
            return "low"
        elif density <= 2.5:
            return "optimal"
        elif density <= 3.5:
            return "high"
        else:
            return "too_high"

    def _score_keyword_usage(self, count: int, density: float, in_title: bool,
                            in_first_para: bool, in_headings: bool, word_count: int) -> int:
        """Score keyword usage out of 100"""
        score = 0

        # Keyword present
        if count > 0:
            score += 15

        # Density scoring
        if 1.0 <= density <= 2.5:
            score += 25  # Optimal
        elif 0.5 <= density < 1.0 or 2.5 < density <= 3.5:
            score += 15  # Acceptable
        elif density > 0:
            score += 5   # Present but not optimal

        # Position scoring
        if in_title:
            score += 20
        if in_first_para:
            score += 20
        if in_headings:
            score += 15

        # Natural usage (not too few, not too many)
        expected_count = max(2, word_count // 200)  # Roughly 1 per 200 words minimum
        if count >= expected_count:
            score += 5

        return min(100, score)

    def _calculate_readability(self, text: str, sentences: int, word_count: int) -> Dict:
        """Calculate readability metrics including Flesch-Kincaid"""
        if word_count == 0 or sentences == 0:
            return {"score": 0, "grade_level": "N/A", "status": "insufficient_content"}

        # Count syllables (approximate)
        syllables = self._count_syllables(text)

        # Flesch Reading Ease
        # 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        avg_sentence_length = word_count / sentences
        avg_syllables_per_word = syllables / word_count

        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))

        # Flesch-Kincaid Grade Level
        # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        grade_level = max(0, grade_level)

        # Determine readability status
        if flesch_score >= 60:
            status = "easy"
        elif flesch_score >= 40:
            status = "moderate"
        else:
            status = "difficult"

        return {
            "flesch_score": round(flesch_score, 1),
            "grade_level": round(grade_level, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "status": status,
            "score": self._score_readability(flesch_score, avg_sentence_length)
        }

    def _count_syllables(self, text: str) -> int:
        """Approximate syllable count"""
        words = text.lower().split()
        total = 0

        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue

            # Count vowel groups
            syllables = len(re.findall(r'[aeiouy]+', word))

            # Adjustments
            if word.endswith('e'):
                syllables -= 1
            if word.endswith('le') and len(word) > 2 and word[-3] not in 'aeiouy':
                syllables += 1
            if syllables == 0:
                syllables = 1

            total += syllables

        return total

    def _score_readability(self, flesch_score: float, avg_sentence_length: float) -> int:
        """Score readability for SEO (targeting general audience)"""
        score = 0

        # Flesch score (target: 60-70 for general web content)
        if flesch_score >= 60:
            score += 60
        elif flesch_score >= 50:
            score += 45
        elif flesch_score >= 40:
            score += 30
        else:
            score += 15

        # Sentence length (target: 15-20 words)
        if 15 <= avg_sentence_length <= 20:
            score += 40
        elif 12 <= avg_sentence_length <= 25:
            score += 25
        else:
            score += 10

        return min(100, score)

    def _analyze_links(self, content: str) -> Dict:
        """Analyze links in content"""
        # Find all markdown links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        links = link_pattern.findall(content)

        internal = []
        external = []

        for text, url in links:
            if url.startswith(('http://', 'https://', 'www.')):
                external.append({"text": text, "url": url})
            else:
                internal.append({"text": text, "url": url})

        return {
            "total": len(links),
            "internal_count": len(internal),
            "external_count": len(external),
            "has_internal": len(internal) > 0,
            "has_external": len(external) > 0,
            "score": self._score_links(len(internal), len(external))
        }

    def _score_links(self, internal: int, external: int) -> int:
        """Score link usage"""
        score = 0

        if internal > 0:
            score += 40  # Has internal links
        if internal >= 2:
            score += 20  # Multiple internal links
        if external > 0:
            score += 25  # Has external/reference links
        if internal > 0 and external > 0:
            score += 15  # Good mix

        return min(100, score)

    def _analyze_images(self, content: str) -> Dict:
        """Analyze images in content"""
        # Find markdown images
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        images = image_pattern.findall(content)

        with_alt = sum(1 for alt, url in images if alt.strip())
        without_alt = len(images) - with_alt

        return {
            "total": len(images),
            "with_alt_text": with_alt,
            "without_alt_text": without_alt,
            "score": self._score_images(len(images), with_alt)
        }

    def _score_images(self, total: int, with_alt: int) -> int:
        """Score image usage"""
        if total == 0:
            return 50  # No images is neutral, not bad

        score = 30  # Has images

        # Alt text percentage
        alt_percentage = with_alt / total
        if alt_percentage == 1:
            score += 70  # All have alt text
        elif alt_percentage >= 0.8:
            score += 50
        elif alt_percentage >= 0.5:
            score += 30

        return min(100, score)

    def _analyze_title(self, title: str, keyword: str = "") -> Dict:
        """Analyze title for SEO"""
        title_length = len(title)

        # Check length
        if 50 <= title_length <= 60:
            length_status = "optimal"
        elif 40 <= title_length < 50 or 60 < title_length <= 70:
            length_status = "acceptable"
        else:
            length_status = "needs_improvement"

        # Check keyword in title
        has_keyword = keyword.lower() in title.lower() if keyword else False
        keyword_at_start = title.lower().startswith(keyword.lower()[:20]) if keyword else False

        return {
            "length": title_length,
            "length_status": length_status,
            "has_keyword": has_keyword,
            "keyword_at_start": keyword_at_start,
            "score": self._score_title(title_length, has_keyword, keyword_at_start)
        }

    def _score_title(self, length: int, has_keyword: bool, keyword_at_start: bool) -> int:
        """Score title for SEO"""
        score = 0

        # Length scoring
        if 50 <= length <= 60:
            score += 40
        elif 40 <= length <= 70:
            score += 25
        elif length > 0:
            score += 10

        # Keyword scoring
        if has_keyword:
            score += 35
        if keyword_at_start:
            score += 25

        return min(100, score)

    def _calculate_comprehensive_seo_score(self, word_count: int, headings: Dict,
                                          keyword_analysis: Dict, readability: Dict,
                                          links: Dict, images: Dict, title_analysis: Dict) -> Dict:
        """Calculate comprehensive SEO score with breakdown"""

        # Content length score
        if word_count >= 1500:
            content_score = 100
        elif word_count >= 1000:
            content_score = 85
        elif word_count >= 600:
            content_score = 70
        elif word_count >= 300:
            content_score = 50
        else:
            content_score = 25

        # Get individual scores
        heading_score = headings.get('score', 0)
        keyword_score = keyword_analysis.get('score', 50) if keyword_analysis else 50
        readability_score = readability.get('score', 50)
        link_score = links.get('score', 0)
        image_score = images.get('score', 50)
        title_score = title_analysis.get('score', 50) if title_analysis else 50

        # Weighted average
        weights = {
            'content': 0.15,
            'headings': 0.15,
            'keywords': 0.25,
            'readability': 0.15,
            'links': 0.10,
            'images': 0.05,
            'title': 0.15
        }

        total_score = (
            content_score * weights['content'] +
            heading_score * weights['headings'] +
            keyword_score * weights['keywords'] +
            readability_score * weights['readability'] +
            link_score * weights['links'] +
            image_score * weights['images'] +
            title_score * weights['title']
        )

        return {
            "total": round(total_score),
            "breakdown": {
                "content_length": {"score": content_score, "weight": "15%"},
                "headings": {"score": heading_score, "weight": "15%"},
                "keywords": {"score": keyword_score, "weight": "25%"},
                "readability": {"score": readability_score, "weight": "15%"},
                "links": {"score": link_score, "weight": "10%"},
                "images": {"score": image_score, "weight": "5%"},
                "title": {"score": title_score, "weight": "15%"}
            },
            "grade": self._get_grade(total_score)
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _identify_issues(self, seo_score: Dict) -> List[Dict]:
        """Identify SEO issues based on scores"""
        issues = []
        breakdown = seo_score.get('breakdown', {})

        # Check each category
        if breakdown.get('content_length', {}).get('score', 100) < 70:
            issues.append({
                "type": "content_length",
                "severity": "medium",
                "message": "Content is shorter than recommended. Aim for 1000+ words for comprehensive coverage.",
                "priority": 2
            })

        if breakdown.get('headings', {}).get('score', 100) < 60:
            issues.append({
                "type": "headings",
                "severity": "medium",
                "message": "Improve heading structure. Use H1 for title, H2 for main sections, H3 for subsections.",
                "priority": 3
            })

        if breakdown.get('keywords', {}).get('score', 100) < 50:
            issues.append({
                "type": "keywords",
                "severity": "high",
                "message": "Keyword optimization needs improvement. Include target keyword in title, first paragraph, and headings.",
                "priority": 1
            })

        if breakdown.get('readability', {}).get('score', 100) < 50:
            issues.append({
                "type": "readability",
                "severity": "medium",
                "message": "Content may be difficult to read. Use shorter sentences and simpler words.",
                "priority": 4
            })

        if breakdown.get('links', {}).get('score', 100) < 40:
            issues.append({
                "type": "links",
                "severity": "low",
                "message": "Add internal links to related content and external links to authoritative sources.",
                "priority": 5
            })

        if breakdown.get('title', {}).get('score', 100) < 60:
            issues.append({
                "type": "title",
                "severity": "high",
                "message": "Optimize title: Keep it 50-60 characters and include your target keyword.",
                "priority": 1
            })

        # Sort by priority
        issues.sort(key=lambda x: x['priority'])

        return issues

    # =========================================
    # KEYWORD RESEARCH (Existing methods updated)
    # =========================================
    def _extract_seed_keywords(self, topic: str, content: str = "") -> List[str]:
        """Use AI to extract main keyword concepts from the blog topic/content"""
        prompt = f"""
        Extract 5-8 seed keywords from this blog topic and content.
        Return ONLY a comma-separated list of keywords, nothing else.

        Topic: {topic}
        Content Preview: {content[:500] if content else 'N/A'}

        Focus on:
        - Main subject keywords
        - Related concepts
        - Long-tail variations
        """

        response = self.model.generate_content(prompt)
        text = (response.text or "") if response else ""
        if not text.strip():
            return [topic.lower()] if topic else []
        keywords = [kw.strip() for kw in text.split(',')]
        return keywords

    def extract_seed_keywords(self, topic: str, content: str) -> List[str]:
        """Public wrapper for seed keyword extraction"""
        return self._extract_seed_keywords(topic, content)

    def get_keyword_data(self, keywords: List[str], region: str = "PK") -> List[Dict]:
        """Fetch keyword metrics using real data sources with caching"""
        # Try cache first (15-minute TTL)
        cache_key = f"keywords:{region}:{':'.join(sorted(keywords[:5]))}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print("Using cached keyword data")
            return cached_result

        # Method 1: Try SEO Keyword Research API (RapidAPI)
        if self.rapidapi_key:
            result = self._fetch_from_seo_api(keywords, region)
            if result:
                print("Using SEO Keyword Research API data")
                cache.set(cache_key, result, ttl=900)  # 15 minutes
                return result

        # Method 2: Try PyTrends as backup
        if self.use_pytrends:
            result = self._fetch_from_pytrends(keywords, region)
            if result:
                print("Using PyTrends (Google Trends) data")
                cache.set(cache_key, result, ttl=900)  # 15 minutes
                return result

        # Method 3: AI-estimated keyword data as final fallback
        result = self._generate_ai_keyword_estimates(keywords, region)
        if result:
            print("Using AI-estimated keyword data (external APIs unavailable)")
            cache.set(cache_key, result, ttl=900)
            return result

        print("ERROR: No keyword data available.")
        return []

    def _fetch_from_seo_api(self, keywords: List[str], region: str) -> List[Dict]:
        """Use SEO Keyword Research API from RapidAPI"""
        try:
            import http.client
            import json

            all_results = []
            country_code = self._get_country_code(region) if region else "us"

            for keyword in keywords[:3]:
                conn = http.client.HTTPSConnection(self.seo_api["host"])

                headers = {
                    'x-rapidapi-key': self.rapidapi_key,
                    'x-rapidapi-host': self.seo_api["host"],
                    'Content-Type': "application/json"
                }

                encoded_keyword = requests.utils.quote(keyword)
                conn.request("GET", f"/keynew.php?keyword={encoded_keyword}&country={country_code}", headers=headers)
                res = conn.getresponse()
                data = res.read()
                conn.close()

                if res.status == 200:
                    json_data = json.loads(data.decode("utf-8"))
                    parsed = self._parse_seo_api_results(json_data, keyword)
                    all_results.extend(parsed)

            return all_results

        except Exception as e:
            print(f"SEO Keyword Research API error: {e}")
            return []

    def _parse_seo_api_results(self, data: list, seed_keyword: str) -> List[Dict]:
        """Parse SEO Keyword Research API results"""
        parsed = []

        if not isinstance(data, list):
            return parsed

        for item in data[:15]:
            keyword_text = item.get('text', '')
            if not keyword_text:
                continue

            volume = item.get('vol', 0) or item.get('v', 0)
            cpc = float(item.get('cpc', 0) or 0)
            competition = item.get('competition', 'medium').lower()
            score = float(item.get('score', 1.0) or 1.0)

            difficulty = self._competition_to_difficulty(competition, score, volume)

            parsed.append({
                "keyword": keyword_text,
                "search_volume": volume,
                "cpc": cpc,
                "competition": competition,
                "difficulty_score": difficulty,
                "source": "seo_api"
            })

        return parsed

    def _competition_to_difficulty(self, competition: str, score: float, volume: int) -> int:
        """Convert API competition data to a 0-100 difficulty score"""
        base = {"low": 25, "medium": 50, "high": 75}.get(competition, 50)
        score_modifier = min(score * 10, 20)
        volume_modifier = min(volume / 50000, 15) if volume > 10000 else 0
        return min(int(base + score_modifier + volume_modifier), 100)

    def _fetch_from_pytrends(self, keywords: List[str], region: str) -> List[Dict]:
        """Use PyTrends (Google Trends)"""
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl='en-US', tz=300)
            geo = self._get_pytrends_geo(region)
            results = []

            for i in range(0, len(keywords), 5):
                batch = keywords[i:i+5]

                try:
                    pytrends.build_payload(batch, geo=geo, timeframe='today 12-m')
                    interest_df = pytrends.interest_over_time()
                    related = pytrends.related_queries()

                    for kw in batch:
                        avg_interest = 0
                        if not interest_df.empty and kw in interest_df.columns:
                            avg_interest = int(interest_df[kw].mean())

                        difficulty = self._estimate_difficulty_from_trends(avg_interest, kw)

                        results.append({
                            "keyword": kw,
                            "search_volume": avg_interest * 100,
                            "competition": self._map_competition(difficulty),
                            "difficulty_score": difficulty,
                            "trend_interest": avg_interest,
                            "source": "google_trends"
                        })

                        if kw in related and related[kw]['rising'] is not None:
                            rising = related[kw]['rising']
                            for _, row in rising.head(3).iterrows():
                                results.append({
                                    "keyword": row['query'],
                                    "search_volume": 500,
                                    "competition": "LOW",
                                    "difficulty_score": 30,
                                    "is_rising": True,
                                    "source": "google_trends_rising"
                                })

                except Exception as e:
                    print(f"PyTrends batch error: {e}")
                    continue

            return results

        except ImportError:
            print("PyTrends not installed. Run: pip install pytrends")
            return []
        except Exception as e:
            print(f"PyTrends error: {e}")
            return []

    def _generate_ai_keyword_estimates(self, keywords: List[str], region: str) -> List[Dict]:
        """Use Gemini to estimate keyword metrics when external APIs are unavailable"""
        try:
            import json
            country = self._get_country_name(region) or region

            prompt = f"""You are an SEO keyword research expert. Estimate realistic keyword metrics for the following keywords targeting {country}.

KEYWORDS: {', '.join(keywords[:8])}

For each keyword, provide:
- keyword: the keyword text
- search_volume: estimated monthly searches (realistic number)
- difficulty_score: SEO difficulty 0-100 (lower = easier to rank)
- competition: LOW, MEDIUM, or HIGH

Also suggest 5 additional related long-tail keywords with low competition.

Return ONLY valid JSON array, no explanation:
[
  {{"keyword": "...", "search_volume": 1000, "difficulty_score": 45, "competition": "MEDIUM"}},
  ...
]"""

            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()

            if not text:
                return []

            if '```' in text:
                json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
                if json_match:
                    text = json_match.group(1).strip()

            start_idx = text.find('[')
            end_idx = text.rfind(']')
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx + 1]

            try:
                results = json.loads(text)
            except json.JSONDecodeError:
                cleaned = re.sub(r',\s*([}\]])', r'\1', text)
                results = json.loads(cleaned)

            for item in results:
                item['source'] = 'ai_estimated'
                if 'difficulty_score' not in item:
                    item['difficulty_score'] = self._estimate_keyword_difficulty(item.get('keyword', ''), region)
                if 'competition' not in item:
                    item['competition'] = self._map_competition(item['difficulty_score'])

            return results

        except Exception as e:
            print(f"AI keyword estimation error: {e}")
            return []

    def _estimate_keyword_difficulty(self, keyword: str, region: str) -> int:
        """Estimate SEO difficulty based on keyword characteristics"""
        base_difficulty = 50
        words = keyword.lower().split()
        word_count = len(words)

        if word_count >= 5:
            base_difficulty -= 30
        elif word_count >= 4:
            base_difficulty -= 25
        elif word_count >= 3:
            base_difficulty -= 15
        elif word_count == 1:
            base_difficulty += 25

        location_terms = ['pakistan', 'lahore', 'karachi', 'islamabad', 'india', 'uk', 'usa']
        if any(loc in keyword.lower() for loc in location_terms):
            base_difficulty -= 20

        question_words = ['how', 'what', 'why', 'when', 'where', 'which', 'who']
        if any(q in words for q in question_words):
            base_difficulty -= 10

        if any(year in keyword for year in ['2024', '2025', '2026']):
            base_difficulty -= 5

        hard_terms = ['best', 'top', 'review', 'vs', 'versus']
        if any(term in words for term in hard_terms):
            base_difficulty += 10

        return max(5, min(95, base_difficulty))

    def _estimate_search_volume(self, keyword: str) -> int:
        """Estimate relative search volume"""
        word_count = len(keyword.split())
        if word_count >= 5:
            return 100
        elif word_count >= 4:
            return 300
        elif word_count >= 3:
            return 800
        elif word_count == 2:
            return 2000
        else:
            return 5000

    def _estimate_difficulty_from_trends(self, interest: int, keyword: str) -> int:
        """Estimate SEO difficulty from Google Trends interest score"""
        base_difficulty = interest
        word_count = len(keyword.split())

        if word_count >= 4:
            base_difficulty = max(10, base_difficulty - 25)
        elif word_count >= 3:
            base_difficulty = max(15, base_difficulty - 15)

        location_terms = ['pakistan', 'lahore', 'karachi', 'islamabad', 'pk']
        if any(loc in keyword.lower() for loc in location_terms):
            base_difficulty = max(10, base_difficulty - 20)

        return min(100, max(0, base_difficulty))

    def _map_competition(self, value) -> str:
        """Map numeric competition to LOW/MEDIUM/HIGH"""
        if isinstance(value, str):
            return value.upper()
        if isinstance(value, float) and value <= 1:
            value = value * 100
        if value <= 33:
            return "LOW"
        elif value <= 66:
            return "MEDIUM"
        else:
            return "HIGH"

    def _get_pytrends_geo(self, region: str) -> str:
        """Convert region code to PyTrends geo code"""
        geo_codes = {
            "PK": "PK", "US": "US", "GB": "GB", "IN": "IN",
            "AE": "AE", "SA": "SA", "CA": "CA", "AU": "AU",
        }
        return geo_codes.get(region, "")

    def _get_country_name(self, region: str) -> str:
        """Convert region code to country name"""
        countries = {
            "PK": "pakistan", "US": "united states", "GB": "united kingdom",
            "IN": "india", "AE": "uae", "SA": "saudi arabia",
            "CA": "canada", "AU": "australia",
        }
        return countries.get(region, "")

    def _get_country_code(self, region: str) -> str:
        """Convert region code to lowercase country code for SEO API"""
        return region.lower() if region else "us"

    def _get_google_related_keywords(self, seed: str, region: str = "PK") -> List[Dict]:
        """Get related keywords for a single seed keyword - wrapper for routes"""
        return self.get_keyword_data([seed], region)

    # =========================================
    # KEYWORD RESEARCH PIPELINE
    # =========================================
    def find_low_competition_keywords(self, topic: str, content: str, region: str = "PK",
                                      max_difficulty: int = 40, min_volume: int = 100) -> Dict:
        """Find low-competition keywords"""
        seed_keywords = self.extract_seed_keywords(topic, content)
        print(f"Seed keywords: {seed_keywords}")

        all_keywords = self.get_keyword_data(seed_keywords, region)

        if not all_keywords:
            return {
                "region": region,
                "primary_keyword": None,
                "secondary_keywords": [],
                "all_opportunities": [],
                "seed_keywords": seed_keywords,
                "error": "No real keyword data available.",
                "data_source": "none"
            }

        low_competition = [
            kw for kw in all_keywords
            if kw['difficulty_score'] <= max_difficulty
            and kw['search_volume'] >= min_volume
        ]

        low_competition.sort(
            key=lambda x: x['search_volume'] / (x['difficulty_score'] + 1),
            reverse=True
        )

        primary = low_competition[0] if low_competition else (all_keywords[0] if all_keywords else None)
        secondary = low_competition[1:4] if len(low_competition) > 1 else []
        data_source = all_keywords[0].get('source', 'unknown') if all_keywords else 'none'

        return {
            "region": region,
            "primary_keyword": primary,
            "secondary_keywords": secondary,
            "all_opportunities": low_competition[:10],
            "all_keywords": all_keywords,
            "seed_keywords": seed_keywords,
            "data_source": data_source
        }

    # =========================================
    # CONTENT OPTIMIZATION
    # =========================================
    def auto_implement_seo(self, title: str, content: str, keyword_data: Dict) -> Dict:
        """Automatically optimize the blog content for SEO"""
        primary_kw = keyword_data.get('primary_keyword', {})
        primary_keyword = primary_kw.get('keyword', '') if primary_kw else ''
        secondary_kws = [kw['keyword'] for kw in keyword_data.get('secondary_keywords', [])]

        prompt = f"""
        You are an SEO expert. Optimize this blog for search engines.

        PRIMARY KEYWORD: {primary_keyword}
        SECONDARY KEYWORDS: {', '.join(secondary_kws)}

        ORIGINAL TITLE: {title}
        ORIGINAL CONTENT:
        {content}

        INSTRUCTIONS:
        1. Rewrite the title to include the primary keyword (keep it 50-60 chars)
        2. Ensure primary keyword appears naturally in the first paragraph
        3. Add the primary keyword to at least one H2 heading
        4. Distribute secondary keywords naturally throughout
        5. Write a meta description (150-160 chars) including primary keyword
        6. Add a FAQ section with 3 relevant questions
        7. Keep content natural and readable - NO keyword stuffing

        RESPOND WITH THIS EXACT JSON FORMAT:
        {{
            "optimized_title": "...",
            "meta_description": "...",
            "optimized_content": "... (full markdown content)",
            "faq_section": [
                {{"question": "...", "answer": "..."}},
                {{"question": "...", "answer": "..."}},
                {{"question": "...", "answer": "..."}}
            ]
        }}

        Return ONLY valid JSON, no explanation.
        """

        try:
            response = None
            import time as _time
            for attempt in range(3):
                try:
                    response = self.model.generate_content(prompt)
                    if response and response.text:
                        break
                except Exception as retry_err:
                    print(f"Gemini attempt {attempt+1} failed: {retry_err}")
                    if attempt < 2:
                        _time.sleep(2)
            if not response or not response.text:
                raise ValueError("Gemini failed to generate content after 3 attempts")
        except Exception as e:
            print(f"Gemini API error in auto_implement_seo: {e}")
            analysis = self.analyze_content(content, title, primary_keyword)
            return {
                "optimized_title": title,
                "meta_description": content[:150],
                "optimized_content": content,
                "seo_analysis": analysis,
                "seo_score": analysis['seo_score']['total'],
                "seo_grade": analysis['seo_score']['grade'],
                "error": str(e)
            }

        try:
            import json
            text = (response.text or "").strip()

            if not text:
                raise ValueError("Gemini returned an empty response")

            # Remove markdown code blocks
            if '```' in text:
                json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
                if json_match:
                    text = json_match.group(1).strip()
                else:
                    text = re.sub(r'^```json?\n?', '', text)
                    text = re.sub(r'\n?```$', '', text)

            # Find the JSON object - look for opening { and matching closing }
            start_idx = text.find('{')
            if start_idx != -1:
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                text = text[start_idx:end_idx]
            else:
                raise ValueError(f"No JSON object found in Gemini response: {text[:200]}")

            # Try parsing as-is first
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                # Clean common issues from AI-generated JSON
                cleaned = text
                # Remove trailing commas before } or ]
                cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                # Replace single quotes with double quotes (but not within already double-quoted strings)
                cleaned = re.sub(r"(?<![\"\\])'([^']*)'(?![\"\\])", r'"\1"', cleaned)
                # Remove JavaScript-style comments
                cleaned = re.sub(r'//[^\n]*', '', cleaned)
                # Fix unescaped newlines inside strings
                cleaned = re.sub(r'(?<=": ")(.*?)(?="[,}\]])', lambda m: m.group(0).replace('\n', '\\n'), cleaned)
                result = json.loads(cleaned)

            # NOW analyze the actual optimized content
            optimized_content = result.get('optimized_content', content)
            optimized_title = result.get('optimized_title', title)

            # Run real analysis on the optimized content
            analysis = self.analyze_content(
                content=optimized_content,
                title=optimized_title,
                target_keyword=primary_keyword
            )

            result['seo_analysis'] = analysis
            result['seo_score'] = analysis['seo_score']['total']
            result['seo_grade'] = analysis['seo_score']['grade']
            result['issues'] = analysis['issues']

            # Add keyword_placement for template compatibility
            keyword_data = analysis.get('keyword_analysis', {})
            result['keyword_placement'] = {
                'in_title': keyword_data.get('in_title', False),
                'in_first_paragraph': keyword_data.get('in_first_paragraph', False),
                'in_headings': keyword_data.get('in_headings', False),
                'density': keyword_data.get('density', 0),
                'count': keyword_data.get('count', 0)
            }

            return result

        except Exception as e:
            print(f"Error parsing SEO response: {e}")
            # Return basic analysis of original content
            analysis = self.analyze_content(content, title, primary_keyword)
            return {
                "optimized_title": title,
                "meta_description": content[:150],
                "optimized_content": content,
                "seo_analysis": analysis,
                "seo_score": analysis['seo_score']['total'],
                "seo_grade": analysis['seo_score']['grade'],
                "error": str(e)
            }

    # =========================================
    # MAIN OPTIMIZATION PIPELINE
    # =========================================
    def analyze_only(self, title: str, content: str, target_keyword: str = "") -> Dict:
        """
        Analyze content without optimization - Step 1 of two-step workflow
        Returns detailed analysis of current SEO status
        """
        print(f"Analyzing content SEO (no optimization)...")

        # Run comprehensive analysis
        analysis = self.analyze_content(content, title, target_keyword)

        # Extract keywords for suggestions (without AI call if no target keyword)
        seed_keywords = []
        if not target_keyword:
            # Simple keyword extraction from title
            words = title.lower().split()
            seed_keywords = [w for w in words if len(w) > 3][:5]

        return {
            "title": title,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "analysis": analysis,
            "seo_score": analysis['seo_score'],
            "issues": analysis['issues'],
            "word_count": analysis['word_count'],
            "readability": analysis['readability'],
            "headings": analysis['headings'],
            "links": analysis['links'],
            "images": analysis['images'],
            "suggested_keywords": seed_keywords,
            "recommendations": self._generate_analysis_recommendations(analysis)
        }

    def _generate_analysis_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations from analysis without keyword data"""
        recommendations = []

        # Score info
        seo_score = analysis.get('seo_score', {})
        total = seo_score.get('total', 0)
        grade = seo_score.get('grade', 'N/A')
        recommendations.append(f"Current SEO Score: {total}/100 (Grade: {grade})")

        # Content length
        word_count = analysis.get('word_count', 0)
        if word_count < 300:
            recommendations.append(f"⚠️ Content too short ({word_count} words). Aim for 1000+ words.")
        elif word_count < 600:
            recommendations.append(f"📝 Content is {word_count} words. Consider expanding to 1000+ for better ranking.")
        else:
            recommendations.append(f"✓ Good content length: {word_count} words")

        # Headings
        headings = analysis.get('headings', {})
        if not headings.get('has_h1'):
            recommendations.append("⚠️ Missing H1 heading - add a main title")
        if not headings.get('has_h2'):
            recommendations.append("⚠️ Missing H2 headings - add section headers")
        if headings.get('proper_hierarchy'):
            recommendations.append("✓ Good heading hierarchy")

        # Readability
        readability = analysis.get('readability', {})
        if readability.get('status') == 'difficult':
            recommendations.append("⚠️ Content may be difficult to read. Use shorter sentences.")
        elif readability.get('status') == 'easy':
            recommendations.append("✓ Good readability score")

        # Links
        links = analysis.get('links', {})
        if links.get('total', 0) == 0:
            recommendations.append("💡 Add internal and external links for better SEO")

        # Issues from analysis
        for issue in analysis.get('issues', [])[:3]:
            if issue['severity'] == 'high':
                recommendations.append(f"🔴 {issue['message']}")

        return recommendations

    # =========================================
    # URL-BASED SEO ANALYSIS (RapidAPI SEO Checker)
    # =========================================
    def analyze_url(self, url: str) -> Dict:
        """
        Analyze a live URL's SEO using the SEO Checker API.
        This is an async API - first call triggers processing, subsequent calls return results.
        """
        import http.client
        import json
        import time

        if not self.rapidapi_key:
            return {"success": False, "error": "RapidAPI key not configured"}

        cache_key = f"seo_url:{url}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        encoded_url = requests.utils.quote(url, safe='')
        headers = {
            'x-rapidapi-key': self.rapidapi_key,
            'x-rapidapi-host': self.seo_checker_api["host"],
            'Content-Type': "application/json"
        }

        try:
            # Poll the API (async endpoint: first call triggers, subsequent returns data)
            for attempt in range(5):
                conn = http.client.HTTPSConnection(self.seo_checker_api["host"])
                conn.request("GET", f"/analyze?url={encoded_url}", headers=headers)
                res = conn.getresponse()
                data = res.read()
                conn.close()

                if res.status != 200:
                    error_msg = json.loads(data.decode("utf-8")).get("message", "API error")
                    return {"success": False, "error": error_msg}

                result = json.loads(data.decode("utf-8"))

                if not result.get("processing"):
                    parsed = self._parse_seo_checker_results(result)
                    cache.set(cache_key, parsed, ttl=1800)  # 30 min cache
                    return parsed

                if attempt < 4:
                    time.sleep(4)

            return {"success": False, "error": "Analysis timed out. Try again in a few seconds."}

        except Exception as e:
            print(f"SEO Checker API error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_seo_checker_results(self, data: Dict) -> Dict:
        """Parse the SEO Checker API response into a structured format"""
        return {
            "success": True,
            "url": data.get("url", ""),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "score": data.get("score", 0),
            "load_time": data.get("loadTime") or data.get("load_time", "N/A"),
            "content_analysis": {
                "word_count": data.get("wordCount") or data.get("word_count", 0),
                "title_length": data.get("titleLength") or data.get("title_length", 0),
                "description_length": data.get("descriptionLength") or data.get("description_length", 0),
                "headings": data.get("headings", {}),
                "images": data.get("images", {}),
                "links": data.get("links", {}),
            },
            "technical": {
                "ssl": data.get("ssl", False),
                "mobile_friendly": data.get("mobileFriendly") or data.get("mobile_friendly", False),
                "robots_txt": data.get("robotsTxt") or data.get("robots_txt", False),
                "sitemap": data.get("sitemap", False),
                "canonical": data.get("canonical", ""),
                "lang": data.get("lang", ""),
            },
            "social": {
                "og_tags": data.get("ogTags") or data.get("og_tags", {}),
                "twitter_tags": data.get("twitterTags") or data.get("twitter_tags", {}),
            },
            "issues": data.get("issues", []),
            "warnings": data.get("warnings", []),
            "passed": data.get("passed", []),
            "raw": data
        }


    def optimize_blog(self, title: str, content: str, region: str = "PK") -> Dict:
        """Complete SEO optimization pipeline"""
        print(f"Starting SEO optimization for region: {region}")

        # Analyze original content first
        original_analysis = self.analyze_content(content, title)
        print(f"Original SEO Score: {original_analysis['seo_score']['total']}/100")

        # Find keywords
        keyword_data = self.find_low_competition_keywords(
            topic=title,
            content=content,
            region=region
        )

        if keyword_data.get('error'):
            return {
                "original": {"title": title, "content": content},
                "original_analysis": original_analysis,
                "keyword_research": keyword_data,
                "optimized": None,
                "error": keyword_data['error'],
                "recommendations": self._generate_recommendations_from_analysis(original_analysis)
            }

        print(f"Found {len(keyword_data.get('all_opportunities', []))} keyword opportunities")

        # Optimize content
        optimized = self.auto_implement_seo(title, content, keyword_data)

        # Calculate improvement
        original_score = original_analysis['seo_score']['total']
        new_score = optimized.get('seo_score', original_score)
        improvement = new_score - original_score

        # Build detailed comparison
        comparison = self._build_comparison(
            original_title=title,
            optimized_title=optimized.get('optimized_title', title),
            original_analysis=original_analysis,
            optimized_analysis=optimized.get('seo_analysis', {}),
            original_score=original_score,
            new_score=new_score
        )

        return {
            "original": {"title": title, "content": content},
            "original_analysis": original_analysis,
            "keyword_research": keyword_data,
            "optimized": optimized,
            "data_source": keyword_data.get('data_source', 'unknown'),
            "score_improvement": improvement,
            "comparison": comparison,
            "changes_made": self._list_changes_made(title, optimized, keyword_data),
            "recommendations": self._generate_recommendations_from_analysis(
                optimized.get('seo_analysis', original_analysis),
                keyword_data
            )
        }

    def _build_comparison(self, original_title: str, optimized_title: str,
                         original_analysis: Dict, optimized_analysis: Dict,
                         original_score: int, new_score: int) -> Dict:
        """Build detailed before/after comparison"""
        original_breakdown = original_analysis.get('seo_score', {}).get('breakdown', {})
        optimized_breakdown = optimized_analysis.get('seo_score', {}).get('breakdown', {})

        return {
            "scores": {
                "before": original_score,
                "after": new_score,
                "improvement": new_score - original_score,
                "improvement_percent": round(((new_score - original_score) / max(original_score, 1)) * 100, 1)
            },
            "grades": {
                "before": original_analysis.get('seo_score', {}).get('grade', 'N/A'),
                "after": optimized_analysis.get('seo_score', {}).get('grade', 'N/A')
            },
            "title": {
                "before": original_title,
                "after": optimized_title,
                "changed": original_title != optimized_title
            },
            "word_count": {
                "before": original_analysis.get('word_count', 0),
                "after": optimized_analysis.get('word_count', 0)
            },
            "readability": {
                "before": original_analysis.get('readability', {}).get('flesch_score', 0),
                "after": optimized_analysis.get('readability', {}).get('flesch_score', 0)
            },
            "breakdown_comparison": {
                "content_length": {
                    "before": original_breakdown.get('content_length', {}).get('score', 0),
                    "after": optimized_breakdown.get('content_length', {}).get('score', 0)
                },
                "headings": {
                    "before": original_breakdown.get('headings', {}).get('score', 0),
                    "after": optimized_breakdown.get('headings', {}).get('score', 0)
                },
                "keywords": {
                    "before": original_breakdown.get('keywords', {}).get('score', 0),
                    "after": optimized_breakdown.get('keywords', {}).get('score', 0)
                },
                "readability": {
                    "before": original_breakdown.get('readability', {}).get('score', 0),
                    "after": optimized_breakdown.get('readability', {}).get('score', 0)
                },
                "links": {
                    "before": original_breakdown.get('links', {}).get('score', 0),
                    "after": optimized_breakdown.get('links', {}).get('score', 0)
                },
                "title": {
                    "before": original_breakdown.get('title', {}).get('score', 0),
                    "after": optimized_breakdown.get('title', {}).get('score', 0)
                }
            }
        }

    def _list_changes_made(self, original_title: str, optimized: Dict, keyword_data: Dict) -> List[Dict]:
        """List all changes made during optimization"""
        changes = []
        primary_kw = keyword_data.get('primary_keyword', {}).get('keyword', 'target keyword')

        # Title change
        new_title = optimized.get('optimized_title', original_title)
        if new_title != original_title:
            changes.append({
                "type": "title",
                "description": "Title optimized with target keyword",
                "before": original_title[:60] + "..." if len(original_title) > 60 else original_title,
                "after": new_title[:60] + "..." if len(new_title) > 60 else new_title
            })

        # Meta description added
        if optimized.get('meta_description'):
            changes.append({
                "type": "meta",
                "description": "Meta description created",
                "before": "None",
                "after": optimized['meta_description'][:80] + "..."
            })

        # Keyword placement
        placement = optimized.get('keyword_placement', {})
        if placement.get('in_title'):
            changes.append({
                "type": "keyword",
                "description": f"Keyword '{primary_kw}' added to title",
                "impact": "high"
            })
        if placement.get('in_first_paragraph'):
            changes.append({
                "type": "keyword",
                "description": f"Keyword '{primary_kw}' added to first paragraph",
                "impact": "high"
            })
        if placement.get('in_headings'):
            changes.append({
                "type": "keyword",
                "description": f"Keyword '{primary_kw}' added to headings",
                "impact": "medium"
            })

        # FAQ added
        if optimized.get('faq_section'):
            changes.append({
                "type": "content",
                "description": f"FAQ section added with {len(optimized['faq_section'])} questions",
                "impact": "medium"
            })

        return changes

    def _generate_recommendations_from_analysis(self, analysis: Dict, keyword_data: Dict = None) -> List[str]:
        """Generate recommendations from actual analysis"""
        recommendations = []

        # Data source info
        if keyword_data:
            data_source = keyword_data.get('data_source', 'unknown')
            if data_source == 'google_trends':
                recommendations.append("Data Source: Google Trends (real search interest data)")
            elif data_source == 'google_related':
                recommendations.append("Data Source: Google Search API")

            primary = keyword_data.get('primary_keyword')
            if primary:
                recommendations.append(
                    f"Target Keyword: '{primary['keyword']}' - "
                    f"Difficulty: {primary['difficulty_score']}/100, "
                    f"Est. Volume: {primary['search_volume']}"
                )

        # Score-based recommendations
        seo_score = analysis.get('seo_score', {})
        total = seo_score.get('total', 0)
        grade = seo_score.get('grade', 'N/A')

        recommendations.append(f"SEO Score: {total}/100 (Grade: {grade})")

        # Specific recommendations from issues
        issues = analysis.get('issues', [])
        for issue in issues[:3]:  # Top 3 issues
            recommendations.append(f"[{issue['severity'].upper()}] {issue['message']}")

        # Readability
        readability = analysis.get('readability', {})
        if readability.get('status') == 'difficult':
            recommendations.append("Consider simplifying your content for better readability.")

        # Content length
        word_count = analysis.get('word_count', 0)
        if word_count < 600:
            recommendations.append(f"Content is {word_count} words. Aim for 1000+ words for better ranking.")
        elif word_count >= 1500:
            recommendations.append(f"Great content length ({word_count} words) for comprehensive coverage.")

        return recommendations


# =========================================
# USAGE EXAMPLE
# =========================================
if __name__ == "__main__":
    agent = SEOAgent()

    title = "Benefits of AI in Healthcare"
    content = """
    # Benefits of AI in Healthcare

    Artificial intelligence is transforming the healthcare industry...

    ## Diagnosis Improvement
    AI can analyze medical images faster than humans...

    ## Treatment Personalization
    Machine learning algorithms can predict patient outcomes...
    """

    result = agent.optimize_blog(title=title, content=content, region="PK")

    print("\n=== ORIGINAL SCORE ===")
    print(f"{result['original_analysis']['seo_score']['total']}/100")

    print("\n=== OPTIMIZED SCORE ===")
    if result.get('optimized'):
        print(f"{result['optimized']['seo_score']}/100 ({result['optimized']['seo_grade']})")

    print("\n=== RECOMMENDATIONS ===")
    for rec in result['recommendations']:
        print(f"• {rec}")
