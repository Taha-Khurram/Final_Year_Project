from flask import Blueprint, render_template, request, jsonify, url_for, session, redirect
from app.agents.blog_agent import BlogAgent
from app.agents.category_agent import CategoryAgent
from app.firebase.firestore_service import FirestoreService
from datetime import datetime
import math

blog_bp = Blueprint('blog', __name__)
db_service = FirestoreService()

# ---------------------------------------------------
# SECURITY MIDDLEWARE
# ---------------------------------------------------

@blog_bp.before_request
def require_login():
    if not session.get('logged_in'):
        return redirect(url_for('auth_bp.login'))

# ---------------------------------------------------
# WEB PAGE ROUTES
# ---------------------------------------------------

# @blog_bp.route('/dashboard')
# def home():
#     try:
#         hour = datetime.now().hour
#         greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"

#         user_id = session.get('user_id')
#         user_role = session.get('user_role', 'USER')
#         username = session.get('user_name', 'User')

#         published_count = db_service.get_published_count(user_id)
#         drafts = db_service.get_blogs_by_status("DRAFT", user_id=user_id)
#         pending = db_service.get_blogs_by_status("UNDER_REVIEW", user_id=user_id)

#         total_blogs = db_service.get_total_blogs_count(user_id=user_id)
#         categories = db_service.get_all_categories(user_id=user_id)
#         recent_activity = db_service.get_recent_activity(user_id=user_id, limit=10)

#         return render_template(
#             'home.html',
#             greeting=greeting,
#             username=username,
#             user_role=user_role,
#             total_blogs_count=total_blogs,
#             published_count=published_count,
#             drafts_count=len(drafts),
#             pending_count=len(pending),
#             categories_count=len(categories),
#             recent_activity=recent_activity
#         )

#     except Exception as e:
#         print(f"Error in home route: {e}")
#         return render_template(
#             'home.html',
#             total_blogs_count=0,
#             published_count=0,
#             drafts_count=0,
#             pending_count=0,
#             recent_activity=[]
#         )

@blog_bp.route('/dashboard')
def home():
    try:
        hour = datetime.now().hour
        greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"

        user_id = session.get('user_id')
        user_role = session.get('user_role', 'USER')
        username = session.get('user_name', 'User')

        published_count = db_service.get_published_count(user_id)
        drafts = db_service.get_blogs_by_status("DRAFT", user_id=user_id)
        pending = db_service.get_blogs_by_status("UNDER_REVIEW", user_id=user_id)

        total_blogs = db_service.get_total_blogs_count(user_id=user_id)
        categories = db_service.get_all_categories(user_id=user_id)
        recent_activity_raw = db_service.get_recent_activity(user_id=user_id, limit=10)

        # Process activities for the template
        recent_activities = []
        for act in recent_activity_raw:
            # Combine action and title for a clean description
            title = act.get('blog_title', '')
            action = act.get('action_text', 'performed an action')
            act['description'] = f"{action} \"{title}\"" if title else action
            recent_activities.append(act)

        return render_template(
            'home.html',
            greeting=greeting,
            username=username,
            total_blogs=total_blogs, # Matches home.html
            published_count=published_count,
            drafts_count=len(drafts),
            pending_count=len(pending),
            recent_activities=recent_activities # Matches home.html
        )

    except Exception as e:
        print(f"Error in home route: {e}")
        return render_template(
            'home.html',
            greeting="Welcome",
            total_blogs=0,
            published_count=0,
            drafts_count=0,
            pending_count=0,
            recent_activities=[]
        )
        
@blog_bp.route('/create')
def create_page():
    return render_template('create_blog.html', username=session.get('user_name', 'User'))


@blog_bp.route('/drafts')
def drafts_page():
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    drafts, total_count = db_service.get_paginated_drafts(user_id, page=page, per_page=per_page)
    total_pages = math.ceil(total_count / per_page) if total_count else 1

    return render_template(
        'drafts.html',
        drafts=drafts,
        current_page=page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@blog_bp.route('/approval')
def approval_page():
    user_id = session.get('user_id')
    user_role = session.get('user_role', 'USER')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if user_role == 'ADMIN':
        pending_blogs = db_service.get_approval_queue(admin_id=user_id)
    else:
        pending_blogs = db_service.get_blogs_by_status("UNDER_REVIEW", user_id=user_id)

    total_count = len(pending_blogs)
    total_pages = math.ceil(total_count / per_page) if total_count else 1

    start = (page - 1) * per_page
    end = start + per_page
    paginated_blogs = pending_blogs[start:end]

    return render_template(
        'approval_queue.html',
        pending_blogs=paginated_blogs,
        current_page=page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@blog_bp.route('/categories')
def categories_page():
    categories = db_service.get_all_categories(user_id=session.get('user_id'))
    return render_template('categories.html', categories=categories)


# ---------------------------------------------------
# API ROUTES
# ---------------------------------------------------

@blog_bp.route('/api/get_blog/<blog_id>')
def get_blog(blog_id):
    try:
        blog_data = db_service.get_blog_by_id(blog_id)
        if not blog_data:
            return jsonify({"success": False, "message": "Blog not found"}), 404

        content = blog_data.get('content', '')
        if isinstance(content, dict):
            content = content.get('body') or content.get('text') or content.get('markdown', '')

        blog_data['content'] = str(content)
        return jsonify({"success": True, "blog": blog_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route('/api/update_blog/<blog_id>', methods=['POST'])
def update_blog(blog_id):
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        success = db_service.update_blog_content(blog_id, title, content)

        if success:
            db_service.log_activity(
                user_id=session.get('user_id'),
                user_name=session.get('user_name', 'User'),
                type="edited",
                action_text="updated blog content",
                blog_title=title
            )

        return jsonify({"success": success})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route('/api/generate', methods=['POST'])
def generate_and_submit():
    try:
        user_id = session.get('user_id')
        user_name = session.get('user_name', 'User')

        if not user_id:
            return jsonify({"success": False, "error": "User session expired"}), 401

        data = request.get_json()
        prompt = data.get('prompt')
        auto_submit = data.get('auto_submit', False)

        blog_ai = BlogAgent()
        generated_data = blog_ai.run_pipeline(prompt)

        # Extract content safely
        content_text = ""
        content_obj = generated_data.get('content', {})

        if isinstance(content_obj, dict):
            content_text = (
                content_obj.get('markdown')
                or content_obj.get('body')
                or content_obj.get('text', '')
            )
        elif isinstance(content_obj, str):
            content_text = content_obj

        if not content_text:
            for value in generated_data.values():
                if isinstance(value, str) and len(value) > len(content_text):
                    content_text = value

        if not content_text:
            content_text = "AI generation completed but content could not be parsed."

        generated_data['content'] = str(content_text)

        # cat_agent = CategoryAgent()
        # generated_data['category'] = cat_agent.categorize_blog(
        #     generated_data.get('title'),
        #     content_text
        # )
        
        # --- CATEGORY ASSIGNMENT (optimized to prevent 504) ---
        cat_agent = CategoryAgent()
        categories = db_service.get_all_categories(user_id,limit=50)
        generated_data['category'] = cat_agent.categorize_blog(
        generated_data.get('title'),
        content_text,
        categories=categories
        )
       

        status = (
            "PUBLISHED"
            if auto_submit and session.get('user_role') == 'ADMIN'
            else "UNDER_REVIEW"
            if auto_submit
            else "DRAFT"
        )

        generated_data['status'] = status
        generated_data['author_id'] = user_id

        db_service.create_draft(generated_data, user_id)

        db_service.log_activity(
            user_id=user_id,
            user_name=user_name,
            type="generated",
            action_text=f"generated a blog as {status}",
            blog_title=generated_data.get('title', 'Untitled')
        )

        return jsonify({
            "success": True,
            "redirect": url_for(
                'blog.approval_page'
                if status == "UNDER_REVIEW"
                else 'blog.home'
                if status == "PUBLISHED"
                else 'blog.drafts_page'
            )
        }), 201

    except Exception as e:
        print(f"❌ Route Error in Generate: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# @blog_bp.route('/api/update_status/<blog_id>', methods=['POST'])
# def update_status(blog_id):
#     try:
#         data = request.get_json()
#         new_status = data.get('status', 'DRAFT').upper()

#         success = db_service.update_blog_status(blog_id, new_status)

#         if success:
#             blog_data = db_service.get_blog_by_id(blog_id)
#             action_text = "approved for publication" if new_status == "PUBLISHED" else "rejected back to drafts"

#             db_service.log_activity(
#                 user_id=session.get('user_id'),
#                 user_name=session.get('user_name', 'Admin'),
#                 type="published" if new_status == "PUBLISHED" else "edited",
#                 action_text=action_text,
#                 blog_title=blog_data.get('title', 'Untitled') if blog_data else "Untitled"
#             )

#         return jsonify({"success": success})

#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route('/api/update_status/<blog_id>', methods=['POST'])
def update_status(blog_id):
    try:
        user_id = session.get('user_id')
        user_role = session.get('user_role', 'USER')
        user_name = session.get('user_name', 'User')

        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.get_json()
        new_status = data.get('status', '').upper()

        allowed_statuses = ["DRAFT", "UNDER_REVIEW", "PUBLISHED"]

        if new_status not in allowed_statuses:
            return jsonify({"success": False, "error": "Invalid status"}), 400

        blog_data = db_service.get_blog_by_id(blog_id)
        if not blog_data:
            return jsonify({"success": False, "error": "Blog not found"}), 404

        # Only admin can publish
        if new_status == "PUBLISHED" and user_role != "ADMIN":
            return jsonify({"success": False, "error": "Only admin can publish"}), 403

        # Only owner or admin can change status
        if blog_data.get("author_id") != user_id and user_role != "ADMIN":
            return jsonify({"success": False, "error": "Not allowed"}), 403

        success = db_service.update_blog_status(blog_id, new_status)

        if not success:
            return jsonify({"success": False, "error": "Status update failed"}), 500

        action_text = (
            "approved for publication"
            if new_status == "PUBLISHED"
            else "submitted for approval"
            if new_status == "UNDER_REVIEW"
            else "moved back to draft"
        )

        db_service.log_activity(
            user_id=user_id,
            user_name=user_name,
            type="status_change",
            action_text=action_text,
            blog_title=blog_data.get('title', 'Untitled')
        )

        return jsonify({"success": True})

    except Exception as e:
        print("❌ Status Update Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route('/api/delete_blog/<blog_id>', methods=['DELETE'])
def delete_blog_api(blog_id):
    blog_data = db_service.get_blog_by_id(blog_id)
    title = blog_data.get('title', 'Untitled') if blog_data else "Untitled"

    success = db_service.delete_blog(blog_id)

    if success:
        db_service.log_activity(
            user_id=session.get('user_id'),
            user_name=session.get('user_name', 'User'),
            type="deleted",
            action_text="permanently deleted",
            blog_title=title
        )

    return jsonify({"success": success})

# Categories API routes
# ---------------------------------------------------
# CATEGORY API ROUTES
# ---------------------------------------------------


@blog_bp.route('/api/categories', methods=['POST'])
def create_category_api():
    try:
        user_id = session.get('user_id')
        if not user_id: return jsonify({"success": False, "error": "Unauthorized"}), 401
        
        data = request.get_json() if request.is_json else request.form
        name = data.get('name', '').strip()
        
        if not name: return jsonify({"success": False, "error": "Category name cannot be empty"}), 400
        
        success, result = db_service.create_category(name, user_id)
        if success:
             return jsonify({"success": True, "id": result, "name": name})
        return jsonify({"success": False, "error": result}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@blog_bp.route('/api/edit_category/<category_id>', methods=['POST'])
def edit_category(category_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.get_json()
        new_name = data.get('name', '').strip()
        if not new_name:
            return jsonify({"success": False, "error": "Category name cannot be empty"}), 400

        # Check if category exists
        category = db_service.get_category_by_id(category_id, user_id=user_id)
        if not category:
            return jsonify({"success": False, "error": "Category not found"}), 404

        # Update category name
        success = db_service.update_category_name(category_id, new_name, user_id=user_id)

        if success:
            db_service.log_activity(
                user_id=user_id,
                user_name=session.get('user_name', 'User'),
                type="edited",
                action_text=f"updated category name to '{new_name}'",
                blog_title=""  # Optional, leave empty for category actions
            )

        return jsonify({"success": success})

    except Exception as e:
        print("❌ Edit Category Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route('/api/delete_category/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        # Check if category exists
        category = db_service.get_category_by_id(category_id, user_id=user_id)
        if not category:
            return jsonify({"success": False, "error": "Category not found"}), 404

        # Optional: Check if any blogs are using this category before deleting
        blogs_in_category = db_service.get_blogs_by_category(category_id, user_id=user_id)
        if blogs_in_category:
            return jsonify({"success": False, "error": "Cannot delete category with assigned blogs"}), 400

        success = db_service.delete_category(category_id, user_id=user_id)

        if success:
            db_service.log_activity(
                user_id=user_id,
                user_name=session.get('user_name', 'User'),
                type="deleted",
                action_text=f"deleted category '{category.get('name')}'",
                blog_title=""  # Optional
            )

        return jsonify({"success": success})

    except Exception as e:
        print("❌ Delete Category Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

