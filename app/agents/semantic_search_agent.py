import numpy as np
import google.generativeai as genai
from flask import current_app
from app.services.embedding_service import EmbeddingService
from app.firebase.firestore_service import FirestoreService
import re
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


class SemanticSearchAgent:
    """
    Optimized Semantic Search Agent

    Performance optimizations:
    1. Parallel query embedding + blog fetching
    2. Fast vector search first, LLM rerank only top results
    3. Simplified prompts for faster LLM response
    4. Timeout handling to prevent slow responses
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.db_service = FirestoreService()
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def _cosine_similarity(self, vec1, vec2):
        """Fast cosine similarity calculation."""
        vec1 = np.array(vec1, dtype=np.float32)
        vec2 = np.array(vec2, dtype=np.float32)
        dot = np.dot(vec1, vec2)
        norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return float(dot / norm) if norm > 0 else 0.0

    def _get_text_content(self, blog):
        """Extract clean text from blog content."""
        content = blog.get('content', '')
        if isinstance(content, dict):
            text = content.get('body', '') or content.get('markdown', '') or ''
        else:
            text = str(content) if content else ''
        return re.sub(r'<[^>]+>', '', text)

    def _get_excerpt(self, blog, max_length=120):
        """Extract clean excerpt without markdown."""
        text = self._get_text_content(blog)
        # Clean markdown
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*?([^*]+)\*\*?', r'\1', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = ' '.join(text.split())

        if len(text) > max_length:
            return text[:max_length].rsplit(' ', 1)[0] + '...'
        return text

    def _keyword_boost(self, blog, query_terms):
        """Fast keyword matching boost."""
        title = blog.get('title', '').lower()
        category = blog.get('category', '').lower()

        boost = 0.0
        for term in query_terms:
            if term in title:
                boost += 0.15
            if term in category:
                boost += 0.1
        return min(boost, 0.3)

    def _rerank_top_results(self, query, candidates):
        """Quick LLM rerank of top candidates only."""
        if not candidates or len(candidates) == 0:
            return candidates

        try:
            # Only rerank top 5 for speed
            to_rerank = candidates[:5]

            posts_info = "\n".join([
                f"{i}. {c.get('title', '')} [{c.get('category', '')}]"
                for i, c in enumerate(to_rerank)
            ])

            prompt = f"""Rate these posts for query "{query}" (0-100). Return JSON only:
{posts_info}

Format: [{{"id":0,"score":85,"why":"brief reason"}},...]"""

            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 300}
            )

            text = response.text.strip()
            text = re.sub(r'^```json?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

            rankings = json.loads(text)

            # Apply rankings
            for rank in rankings:
                idx = rank.get('id', 0)
                if idx < len(to_rerank):
                    to_rerank[idx]['score'] = rank.get('score', 50) / 100
                    to_rerank[idx]['match_reason'] = rank.get('why', '')

            # Sort by new score
            to_rerank.sort(key=lambda x: x.get('score', 0), reverse=True)

            # Add remaining candidates
            return to_rerank + candidates[5:]

        except Exception as e:
            print(f"Rerank error: {e}")
            return candidates

    def search(self, user_id, query, top_k=6):
        """
        Optimized semantic search pipeline.
        """
        try:
            if not query or len(query) < 2:
                return []

            query_lower = query.lower()
            query_terms = [t.strip() for t in query_lower.split() if len(t.strip()) > 2]

            # Parallel: get embedding + fetch blogs
            with ThreadPoolExecutor(max_workers=2) as executor:
                embedding_future = executor.submit(
                    self.embedding_service.generate_query_embedding, query
                )
                blogs_future = executor.submit(
                    self.db_service.get_blogs_with_embeddings, user_id
                )

                query_embedding = embedding_future.result(timeout=5)
                blogs = blogs_future.result(timeout=5)

            if not blogs:
                # Fallback to all published blogs
                blogs = self.db_service.get_published_blogs(user_id, limit=30)

            # Fast vector scoring
            candidates = []
            for blog in blogs:
                blog_embedding = blog.get('embedding')

                # Vector similarity
                vec_score = 0.0
                if query_embedding and blog_embedding:
                    vec_score = self._cosine_similarity(query_embedding, blog_embedding)

                # Keyword boost
                keyword_boost = self._keyword_boost(blog, query_terms)

                # Combined score
                score = vec_score + keyword_boost

                if score > 0.25 or keyword_boost > 0.1:
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

            # Sort by initial score
            candidates.sort(key=lambda x: x['score'], reverse=True)

            # Quick LLM rerank top results
            if candidates:
                candidates = self._rerank_top_results(query, candidates)

            return candidates[:top_k]

        except FuturesTimeoutError:
            print("Search timeout - returning fast results")
            return []
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
