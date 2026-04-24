import numpy as np
import google.generativeai as genai
from flask import current_app
from app.services.embedding_service import EmbeddingService
from app.firebase.firestore_service import FirestoreService
import re
import json


class SemanticSearchAgent:
    """
    Semantic Search Agent with keyword fallback.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.db_service = FirestoreService()
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity."""
        vec1 = np.array(vec1, dtype=np.float32)
        vec2 = np.array(vec2, dtype=np.float32)
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return float(dot / norm) if norm > 0 else 0.0

    def _get_text_content(self, blog):
        """Extract text from blog content."""
        content = blog.get('content', '')
        if isinstance(content, dict):
            text = content.get('body', '') or content.get('markdown', '') or ''
        else:
            text = str(content) if content else ''
        return re.sub(r'<[^>]+>', '', text).lower()

    def _get_excerpt(self, blog, max_length=120):
        """Extract clean excerpt."""
        content = blog.get('content', '')
        if isinstance(content, dict):
            text = content.get('body', '') or content.get('markdown', '') or ''
        else:
            text = str(content) if content else ''

        # Clean markdown and HTML
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*?([^*]+)\*\*?', r'\1', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = ' '.join(text.split())

        if len(text) > max_length:
            return text[:max_length].rsplit(' ', 1)[0] + '...'
        return text

    def _keyword_score(self, blog, query_terms):
        """Calculate keyword match score."""
        title = blog.get('title', '').lower()
        category = blog.get('category', '').lower()
        content = self._get_text_content(blog)

        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.3
            if term in category:
                score += 0.2
            if term in content:
                score += 0.1
        return min(score, 1.0)

    def _rerank_with_llm(self, query, candidates):
        """Rerank top results with LLM."""
        if not candidates:
            return candidates

        try:
            to_rerank = candidates[:5]
            posts_info = "\n".join([
                f"{i}. {c.get('title', '')} [{c.get('category', '')}]"
                for i, c in enumerate(to_rerank)
            ])

            prompt = f"""Rate these blog posts for the search query "{query}".

Posts:
{posts_info}

Return a JSON array with scores (0-100) and brief reasons. Use this exact format:
[
  {{"id": 0, "score": 85, "why": "Directly addresses the topic"}},
  {{"id": 1, "score": 60, "why": "Related but not specific"}}
]

Only return the JSON array, nothing else."""

            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 400}
            )

            text = response.text.strip()

            # Clean up response
            text = re.sub(r'^```json?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()

            # Fix common JSON issues
            text = text.replace("'", '"')  # Single to double quotes

            rankings = json.loads(text)

            for rank in rankings:
                idx = rank.get('id', 0)
                if idx < len(to_rerank):
                    to_rerank[idx]['score'] = rank.get('score', 50) / 100
                    to_rerank[idx]['match_reason'] = rank.get('why', '')

            to_rerank.sort(key=lambda x: x.get('score', 0), reverse=True)
            return to_rerank + candidates[5:]

        except Exception as e:
            print(f"Rerank error: {e}")
            # Return with default reasons based on score
            for c in candidates:
                if not c.get('match_reason'):
                    c['match_reason'] = f"Matches your search"
            return candidates

    def search(self, user_id, query, top_k=6):
        """Search blogs using keywords + optional vector similarity."""
        try:
            if not query or len(query) < 2:
                return []

            query_lower = query.lower()
            query_terms = [t.strip() for t in query_lower.split() if len(t.strip()) > 2]

            # Get all published blogs
            blogs = self.db_service.get_published_blogs(user_id, limit=50)

            if not blogs:
                return []

            # Try to get query embedding (non-blocking)
            query_embedding = None
            try:
                query_embedding = self.embedding_service.generate_query_embedding(query)
            except Exception as e:
                print(f"Embedding error (using keywords only): {e}")

            # Score all blogs
            candidates = []
            for blog in blogs:
                # Keyword score (always works)
                kw_score = self._keyword_score(blog, query_terms)

                # Vector score (if available)
                vec_score = 0.0
                blog_embedding = blog.get('embedding')
                if query_embedding and blog_embedding:
                    vec_score = self._cosine_similarity(query_embedding, blog_embedding)

                # Combined score
                if vec_score > 0:
                    score = (vec_score * 0.6) + (kw_score * 0.4)
                else:
                    score = kw_score

                # Include if any relevance
                if score > 0.1:
                    candidates.append({
                        'id': blog.get('id'),
                        'title': blog.get('title', ''),
                        'category': blog.get('category', ''),
                        'excerpt': self._get_excerpt(blog),
                        'cover_image': blog.get('cover_image_url', ''),
                        'score': round(score, 3),
                        'match_reason': '',
                        'updated_at': blog.get('updated_at')
                    })

            if not candidates:
                return []

            # Sort by score
            candidates.sort(key=lambda x: x['score'], reverse=True)

            # LLM rerank top results
            candidates = self._rerank_with_llm(query, candidates)

            return candidates[:top_k]

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def generate_and_store_embedding(self, blog_id):
        """Generate and store embedding for a blog."""
        try:
            blog = self.db_service.get_blog_by_id(blog_id)
            if not blog:
                return False

            embedding = self.embedding_service.generate_blog_embedding(blog)
            if not embedding:
                return False

            return self.db_service.update_blog_embedding(blog_id, embedding)
        except Exception as e:
            print(f"Embedding error: {e}")
            return False
