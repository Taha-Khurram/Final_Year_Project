from flask import Blueprint, render_template, abort
from app.firebase.firestore_service import FirestoreService
import markdown

site_bp = Blueprint('site_bp', __name__, url_prefix='/site')
db_service = FirestoreService()


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

        return render_template(
            'site/site_home.html',
            settings=settings,
            blogs=published_blogs,
            categories=categories,
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

        # Verify blog belongs to this user
        if blog.get('author_id') != user_id:
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

        return render_template(
            'site/site_post.html',
            settings=settings,
            blog=blog,
            related_blogs=related_blogs,
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
