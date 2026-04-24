from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify
from app.firebase.firestore_service import FirestoreService
import markdown
import math

site_bp = Blueprint('site_bp', __name__, url_prefix='/site')
db_service = FirestoreService()


def _get_blog_text_content(blog):
    """Extract searchable text content from a blog post"""
    content = blog.get('content', '')
    if isinstance(content, dict):
        return content.get('body', '') or content.get('markdown', '') or content.get('text', '')
    return str(content) if content else ''


# ---------------------------------------------------
# PUBLIC SITE ROUTES (No authentication required)
# ---------------------------------------------------

@site_bp.route('/<user_id>')
def site_home(user_id):
    """Public site homepage - displays published blogs"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Get published blogs using dynamic posts_per_page setting
        posts_limit = settings.get('posts_per_page', 10)
        published_blogs = db_service.get_published_blogs(user_id, limit=posts_limit)

        # Get categories for filtering
        categories = db_service.get_all_categories(user_id=user_id)

        # Get featured post if set
        featured_post = None
        if settings.get('featured_post_id'):
            featured_post = db_service.get_published_blog_by_id(settings['featured_post_id'])

        return render_template(
            'site/site_home.html',
            settings=settings,
            blogs=published_blogs,
            categories=categories,
            featured_post=featured_post,
            user_id=user_id
        )

    except Exception as e:
        print(f"Site Home Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/post/<blog_id>')
def site_post(user_id, blog_id):
    """Single blog post view"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Get the published blog
        blog = db_service.get_published_blog_by_id(blog_id)

        if not blog:
            abort(404)

        # Verify blog belongs to this site (by site_owner_id, not author_id)
        if blog.get('site_owner_id') != user_id and blog.get('author_id') != user_id:
            abort(404)

        # Process content for display
        content = blog.get('content', '')
        if isinstance(content, dict):
            html_content = content.get('html', '')
            if not html_content:
                # Convert markdown to HTML if needed
                md_content = content.get('markdown') or content.get('body') or ''
                html_content = markdown.markdown(md_content, extensions=['extra', 'tables', 'toc'])
            blog['html_content'] = html_content
            blog['toc'] = content.get('toc', [])
            blog['toc_html'] = content.get('toc_html', '')
        else:
            blog['html_content'] = markdown.markdown(str(content), extensions=['extra', 'tables'])
            blog['toc'] = []
            blog['toc_html'] = ''

        # Get related blogs (same category)
        related_blogs = []
        if blog.get('category'):
            all_published = db_service.get_published_blogs(user_id, limit=10)
            related_blogs = [
                b for b in all_published
                if b.get('category') == blog.get('category') and b.get('id') != blog_id
            ][:3]

        # Get categories for footer
        categories = db_service.get_all_categories(user_id=user_id)

        return render_template(
            'site/site_post.html',
            settings=settings,
            blog=blog,
            related_blogs=related_blogs,
            categories=categories,
            user_id=user_id
        )

    except Exception as e:
        print(f"Site Post Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/about')
def site_about(user_id):
    """About page with site description"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Get stats
        published_blogs = db_service.get_published_blogs(user_id, limit=100)
        categories = db_service.get_all_categories(user_id=user_id)

        return render_template(
            'site/site_about.html',
            settings=settings,
            published_count=len(published_blogs),
            categories_count=len(categories),
            categories=categories,
            user_id=user_id
        )

    except Exception as e:
        print(f"Site About Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/category/<category_name>')
def site_category(user_id, category_name):
    """Filter blogs by category"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Get published blogs using dynamic posts_per_page setting
        posts_limit = settings.get('posts_per_page', 10)
        all_published = db_service.get_published_blogs(user_id, limit=posts_limit)

        # Filter by category
        filtered_blogs = [
            b for b in all_published
            if b.get('category', '').lower() == category_name.lower()
        ]

        # Get all categories for sidebar
        categories = db_service.get_all_categories(user_id=user_id)

        return render_template(
            'site/site_home.html',
            settings=settings,
            blogs=filtered_blogs,
            categories=categories,
            user_id=user_id,
            current_category=category_name
        )

    except Exception as e:
        print(f"Site Category Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/blog')
def site_blog(user_id):
    """Dedicated blog listing page with pagination and search"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Pagination and filter parameters
        page = request.args.get('page', 1, type=int)
        per_page = settings.get('posts_per_page', 12)
        category = request.args.get('category', None)
        search_query = request.args.get('search', '').strip()

        # Get all published blogs
        all_blogs = db_service.get_published_blogs(user_id, limit=100)

        # Filter by search query if provided
        if search_query:
            search_lower = search_query.lower()
            all_blogs = [
                b for b in all_blogs
                if search_lower in b.get('title', '').lower()
                or search_lower in _get_blog_text_content(b).lower()
                or search_lower in b.get('category', '').lower()
            ]

        # Filter by category if provided
        if category:
            all_blogs = [
                b for b in all_blogs
                if b.get('category', '').lower() == category.lower()
            ]

        # Calculate pagination
        total_posts = len(all_blogs)
        total_pages = math.ceil(total_posts / per_page) if total_posts > 0 else 1
        start = (page - 1) * per_page
        paginated_blogs = all_blogs[start:start + per_page]

        # Get categories for sidebar
        categories = db_service.get_all_categories(user_id=user_id)

        return render_template(
            'site/site_blog.html',
            settings=settings,
            blogs=paginated_blogs,
            categories=categories,
            current_category=category,
            search_query=search_query,
            current_page=page,
            total_pages=total_pages,
            total_posts=total_posts,
            per_page=per_page,
            user_id=user_id
        )

    except Exception as e:
        print(f"Site Blog Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/contact')
def site_contact(user_id):
    """Contact page"""
    try:
        # Get site settings
        settings = db_service.get_site_settings(user_id)

        # Get categories for footer
        categories = db_service.get_all_categories(user_id=user_id)

        return render_template(
            'site/site_contact.html',
            settings=settings,
            categories=categories,
            user_id=user_id
        )

    except Exception as e:
        print(f"Site Contact Error: {e}")
        abort(404)


@site_bp.route('/<user_id>/contact', methods=['POST'])
def site_contact_submit(user_id):
    """Handle contact form submission"""
    try:
        data = request.form
        db_service.save_contact_submission(user_id, {
            'name': data.get('name'),
            'email': data.get('email'),
            'subject': data.get('subject'),
            'message': data.get('message')
        })
        # Redirect back with success message
        return redirect(url_for('site_bp.site_contact', user_id=user_id, success=1))
    except Exception as e:
        print(f"Contact Submit Error: {e}")
        return redirect(url_for('site_bp.site_contact', user_id=user_id, error=1))


@site_bp.route('/<user_id>/subscribe', methods=['POST'])
def site_subscribe(user_id):
    """Handle newsletter subscription"""
    try:
        email = request.form.get('email', '').strip()
        if email and '@' in email:
            doc_id, is_new = db_service.save_newsletter_subscriber(user_id, email)
            if doc_id:
                if is_new:
                    return jsonify({'success': True, 'is_new': True, 'message': 'Subscribed successfully!'})
                else:
                    return jsonify({'success': True, 'is_new': False, 'message': 'Already subscribed!'})
            return jsonify({'success': False, 'message': 'Subscription failed'}), 500
        return jsonify({'success': False, 'message': 'Invalid email'}), 400
    except Exception as e:
        print(f"Subscribe Error: {e}")
        return jsonify({'success': False, 'message': 'Subscription failed'}), 500


@site_bp.route('/<user_id>/semantic-search', methods=['POST'])
def site_semantic_search(user_id):
    """
    Semantic search API endpoint.
    Accepts a JSON body with 'query' field and returns semantically relevant blogs.
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip() if data else ''

        if not query:
            return jsonify({'success': False, 'message': 'Query is required', 'results': []}), 400

        if len(query) < 2:
            return jsonify({'success': False, 'message': 'Query too short', 'results': []}), 400

        # Import here to avoid circular imports
        from app.agents.semantic_search_agent import SemanticSearchAgent

        search_agent = SemanticSearchAgent()
        results, insights = search_agent.search(user_id, query, top_k=6, include_insights=True)

        # Format results for frontend
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['id'],
                'title': result['title'],
                'category': result.get('category', ''),
                'excerpt': result.get('excerpt', ''),
                'cover_image': result.get('cover_image', ''),
                'score': result.get('score', 0),
                'match_reason': result.get('match_reason', ''),
                'url': url_for('site_bp.site_post', user_id=user_id, blog_id=result['id'])
            })

        return jsonify({
            'success': True,
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'insights': insights
        })

    except Exception as e:
        print(f"Semantic Search Error: {e}")
        return jsonify({'success': False, 'message': 'Search failed', 'results': []}), 500
