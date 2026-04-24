import numpy as np
from app.services.embedding_service import EmbeddingService
from app.firebase.firestore_service import FirestoreService
import re


class SemanticSearchAgent:
    """
    Semantic Search Agent with keyword fallback.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.db_service = FirestoreService()

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

    def _generate_match_reason(self, blog, query_terms):
        """Generate a match reason based on where keywords matched."""
        title = blog.get('title', '').lower()
        category = blog.get('category', '').lower()

        matched_in_title = [t for t in query_terms if t in title]
        matched_in_category = [t for t in query_terms if t in category]

        if matched_in_title:
            if len(matched_in_title) > 1:
                return f"Title contains '{matched_in_title[0]}' and related terms"
            return f"Title mentions '{matched_in_title[0]}'"
        elif matched_in_category:
            return f"In the '{blog.get('category', '')}' category"
        else:
            return "Related to your search topic"

    def _rerank_with_llm(self, query, candidates):
        """Generate match reasons for top results."""
        if not candidates:
            return candidates

        query_terms = [t.strip() for t in query.lower().split() if len(t.strip()) > 2]

        # Generate reasons based on actual matches (fast and reliable)
        for c in candidates:
            blog_data = {'title': c.get('title', ''), 'category': c.get('category', '')}
            c['match_reason'] = self._generate_match_reason(blog_data, query_terms)

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
