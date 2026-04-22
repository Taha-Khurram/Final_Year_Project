from datetime import datetime
from app.firebase.firebase_admin import FirebaseLoader
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from app.utils.cache import cache

class FirestoreService:
    def __init__(self):
        self.db = FirebaseLoader.get_instance()
        self.collection_name = "blogs"
        self.activity_collection = "activities"
        self.user_collection = "users" 

    # ---------------- BLOG METHODS ----------------

    def get_blog_by_id(self, blog_id):
        """Fetches a blog and ensures content is a string so TinyMCE can display it."""
        try:
            doc = self.db.collection(self.collection_name).document(blog_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # --- FIX: ROBUST CONTENT HANDLING ---
                raw_content = data.get('content', '')
                
                if raw_content is None:
                    data['content'] = ""
                elif isinstance(raw_content, dict):
                    # If content was accidentally saved as a map/dict, extract known keys
                    data['content'] = raw_content.get('body', raw_content.get('text', ''))
                else:
                    # Ensure it is a string (prevents issues if it's an int or other type)
                    data['content'] = str(raw_content)
                # ------------------------------------
                    
                return data
            return None
        except Exception as e:
            print(f"❌ Error fetching blog {blog_id}: {e}")
            return None

    def create_draft(self, blog_data, user_id):
        """Saves blog as DRAFT and increments category count."""
        try:
            blog_data['created_at'] = firestore.SERVER_TIMESTAMP
            blog_data['updated_at'] = datetime.utcnow()
            blog_data['author_id'] = user_id 
            blog_data['status'] = blog_data.get('status', 'DRAFT').upper()

            doc_ref = self.db.collection(self.collection_name).add(blog_data)
            blog_id = doc_ref[1].id

            category_name = blog_data.get('category')
            if category_name:
                self.update_category_count(category_name, 1, user_id)

            return blog_id
        except Exception as e:
            print(f"❌ Firestore Error creating draft: {e}")
            return None

    def update_blog_content(self, blog_id, title, content):
        """Updates the title and body content of a blog post."""
        try:
            doc_ref = self.db.collection(self.collection_name).document(blog_id)
            # Save content as a string to match TinyMCE output
            doc_ref.update({
                'title': title,
                'content': content, 
                'updated_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"❌ Error updating blog content: {e}")
            return False

    # def update_blog_status(self, blog_id, status):
    #     try:
    #         doc_ref = self.db.collection(self.collection_name).document(blog_id)
    #         doc_ref.update({
    #             'status': status.upper(),
    #             'updated_at': datetime.utcnow()
    #         })
    #         return True
    #     except Exception as e:
    #         print(f"❌ Error updating status: {e}")
    #         return False
    

    def get_blogs_by_status(self, status, user_id):
        """Filters blogs by status AND author."""
        try:
            docs = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('author_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', status.upper())).stream()
            
            blogs = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                blogs.append(data)
            return blogs
        except Exception as e:
            print(f"❌ Error fetching blogs by status {status}: {e}")
            return []

    # def get_approval_queue(self, admin_id):
    #     """Fetches blogs pending approval from users created by this specific admin."""
    #     try:
    #         sub_users = self.db.collection(self.user_collection)\
    #             .where(filter=FieldFilter('created_by', '==', admin_id)).stream()
    #         uids = [u.id for u in sub_users]
            
    #         if not uids:
    #             return []

    #         docs = self.db.collection(self.collection_name)\
    #             .where(filter=FieldFilter('status', '==', 'PENDING_APPROVAL'))\
    #             .where(filter=FieldFilter('author_id', 'in', uids)).stream()
            
    #         return [{**doc.to_dict(), 'id': doc.id} for doc in docs]
    #     except Exception as e:
    #         print(f"❌ Error fetching approval queue: {e}")
    #         return []
    
     
    # def get_approval_queue(self):
    #     try:
    #         docs = (
    #             self.db.collection("blogs")
    #             .where("status", "==", "UNDER_REVIEW")
    #             .order_by("updated_at", direction=firestore.Query.DESCENDING)
    #             .stream()
    #         )

    #         blogs = []
    #         for doc in docs:
    #             data = doc.to_dict()
    #             data["id"] = doc.id
    #             blogs.append(data)

    #         return blogs

    #     except Exception as e:
    #         print("Approval Queue Error:", e)
    #         return []
    
    
    def get_approval_queue(self, admin_id):
        """
        Returns pending blogs for an admin's approval queue:
        - Blogs submitted by the admin themselves
        - Blogs submitted by users created by this admin
        """
        try:
            # Step 1: Get users created by this admin
            users_ref = self.db.collection("users")
            user_docs = users_ref.where("created_by", "==", admin_id).stream()
            user_ids = [user.id for user in user_docs]

            # Include admin themselves
            user_ids.append(admin_id)

            # Step 2: Fetch pending blogs for these users (batched if needed)
            blogs_ref = self.db.collection("blogs")
            pending_blogs = []

            batch_size = 10  # Firestore 'in' query limit
            for i in range(0, len(user_ids), batch_size):
                batch_ids = user_ids[i:i + batch_size]
                docs = (
                    blogs_ref
                    .where("author_id", "in", batch_ids)
                    .where("status", "==", "UNDER_REVIEW")
                    .order_by("updated_at", direction=firestore.Query.DESCENDING)
                    .stream()
                )
                for doc in docs:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    pending_blogs.append(data)

            return pending_blogs

        except Exception as e:
            print("Approval Queue Error:", e)
            return []
    def get_total_blogs_count(self, user_id):
        try:
            count_query = self.db.collection(self.collection_name)\
                                     .where(filter=FieldFilter('author_id', '==', user_id)).count()
            count_result = count_query.get()
            return count_result[0][0].value
        except Exception as e:
            print(f"❌ Error getting total blogs count: {e}")
            return 0

    def get_paginated_drafts(self, user_id, page=1, per_page=10):
        try:
            skip = (page - 1) * per_page
            query = self.db.collection(self.collection_name)\
                           .where(filter=FieldFilter('author_id', '==', user_id))\
                           .where(filter=FieldFilter('status', '==', 'DRAFT'))\
                           .order_by('updated_at', direction=firestore.Query.DESCENDING)\
                           .offset(skip)\
                           .limit(per_page)
            
            drafts = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                drafts.append(data)

            total_count_query = self.db.collection(self.collection_name)\
                                           .where(filter=FieldFilter('author_id', '==', user_id))\
                                           .where(filter=FieldFilter('status', '==', 'DRAFT'))\
                                           .count()
            total_count = total_count_query.get()[0][0].value

            return drafts, total_count
        except Exception as e:
            print(f"❌ Error fetching paginated drafts: {e}")
            return [], 0

    def delete_blog(self, blog_id):
        try:
            blog_ref = self.db.collection(self.collection_name).document(blog_id)
            blog_snap = blog_ref.get()
            if not blog_snap.exists:
                return False

            blog_data = blog_snap.to_dict()
            category_name = blog_data.get("category")
            user_id = blog_data.get("author_id")

            @firestore.transactional
            def delete_in_transaction(transaction):
                if category_name and user_id:
                    cat_query = self.db.collection("categories")\
                        .where(filter=FieldFilter("name", "==", category_name))\
                        .where(filter=FieldFilter("created_by", "==", user_id)).limit(1)
                    cat_docs = cat_query.get(transaction=transaction)
                    if len(cat_docs) > 0:
                        transaction.update(cat_docs[0].reference, {"count": firestore.Increment(-1)})
                transaction.delete(blog_ref)
                return True

            transaction = self.db.transaction()
            return delete_in_transaction(transaction)
        except Exception as e:
            print(f"❌ Error deleting blog: {e}")
            return False

    # ---------------- CATEGORY METHODS ----------------

    # def get_all_categories(self, user_id=None):
    #     try:
    #         query = self.db.collection("categories")
    #         if user_id:
    #             query = query.where(filter=FieldFilter("created_by", "==", user_id))
                
    #         docs = query.stream()
    #         categories = []
    #         for doc in docs:
    #             data = doc.to_dict()
    #             data['id'] = doc.id
    #             categories.append(data)
    #         return categories 
    #     except Exception as e:
    #         print(f"❌ Error fetching categories: {e}")
    #         return []
    
    # Inside FirestoreService
    def get_category_names(self):
        """Fetch only category names for AI categorization."""
        try:
            docs = self.db.collection("categories").select(["name"]).stream()
            return [doc.to_dict()["name"] for doc in docs]
        except Exception as e:
            print(f"❌ FirestoreService.get_category_names Error: {e}")
            return []
        
    # def get_all_categories(self, user_id=None):
    #     """
    #     Fetches all categories, only returns 'name' field.
    #     Optional filter by user_id (maps to 'created_by').
    #     """
    #     try:
    #         query = self.db.collection("categories")
    #         if user_id:
    #             query = query.where("created_by", "==", user_id)  # FIX: was 'user_id'
    #         docs = query.select(["name"]).stream()
    #         return [{"name": doc.to_dict()["name"]} for doc in docs]
    #     except Exception as e:
    #         print(f"❌ FirestoreService.get_all_categories Error: {e}")
    #         return []
    
    
    def get_all_categories(self, user_id=None, limit=None, use_cache=True):
        """
        Fetch all categories with id, name, and count.
        Optional limit to prevent timeouts.
        Caches results for 5 minutes by default.
        """
        # Try cache first
        if use_cache and user_id:
            cache_key = f"categories:{user_id}:{limit}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        try:
            query = self.db.collection("categories")
            if user_id:
                query = query.where(filter=FieldFilter("created_by", "==", user_id))
            if limit:
                query = query.limit(limit)
            docs = query.stream()
            categories = []
            for doc in docs:
                data = doc.to_dict()
                categories.append({
                    "id": doc.id,
                    "name": data.get("name"),
                    "count": data.get("count", 0)
                })

            # Cache the result for 5 minutes
            if use_cache and user_id:
                cache.set(cache_key, categories, ttl=300)

            return categories
        except Exception as e:
            print(f"❌ FirestoreService.get_all_categories Error: {e}")
            return []

    def update_category_count(self, category_name, increment_by, user_id):
        try:
            cat_query = self.db.collection("categories")\
                .where(filter=FieldFilter("name", "==", category_name))\
                .where(filter=FieldFilter("created_by", "==", user_id)).limit(1).get()

            if cat_query:
                cat_ref = cat_query[0].reference
                cat_ref.update({"count": firestore.Increment(increment_by)})
            else:
                # Create new category
                self.db.collection("categories").add({
                    "name": category_name,
                    "count": 1 if increment_by > 0 else 0,
                    "created_by": user_id,
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                # Invalidate category cache since we created a new one
                cache.clear_prefix(f"categories:{user_id}")
        except Exception as e:
            print(f"❌ Error updating category count: {e}")

    def delete_category(self, category_id, user_id):
        """
        Deletes a category only if it belongs to the user.
        """
        try:
            doc_ref = self.db.collection("categories").document(category_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            # Only allow deletion if created_by matches current user
            if doc.to_dict().get("created_by") != user_id:
                return False
            doc_ref.delete()

            # Invalidate category cache for this user
            cache.clear_prefix(f"categories:{user_id}")

            return True
        except Exception as e:
            print(f"❌ Error deleting category: {e}")
            return False

    def update_category(self, category_id, update_data):
        try:
            doc_ref = self.db.collection("categories").document(category_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"❌ Error updating category: {e}")
            return False

    # ---------------- ACTIVITY METHODS ----------------

    def log_activity(self, user_id, user_name, type, action_text, blog_title):
        try:
            doc_ref = self.db.collection(self.activity_collection).document()
            doc_ref.set({
                "user_id": user_id,
                "user_name": user_name,
                "type": type,
                "action_text": action_text,
                "blog_title": blog_title,
                "timestamp": datetime.utcnow(),
                "created_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False

    def get_recent_activity(self, user_id, limit=10):
        try:
            docs = (self.db.collection(self.activity_collection)
                        .where(filter=FieldFilter("user_id", "==", user_id))
                        .order_by("timestamp", direction=firestore.Query.DESCENDING)
                        .limit(limit)
                        .stream())
            activities = []
            now = datetime.utcnow()
            for doc in docs:
                data = doc.to_dict()
                if 'timestamp' in data:
                    ts = data['timestamp'].replace(tzinfo=None)
                    diff = now - ts
                    if diff.days > 0:
                        data['timestamp'] = f"{diff.days}d ago"
                    elif diff.seconds > 3600:
                        data['timestamp'] = f"{diff.seconds // 3600}h ago"
                    elif diff.seconds > 60:
                        data['timestamp'] = f"{diff.seconds // 60}m ago"
                    else:
                        data['timestamp'] = "Just now"
                activities.append(data)
            return activities
        except Exception as e:
            print(f"❌ Error fetching activities: {e}")
            return []

    # ---------------- USER METHODS ----------------

    def save_user(self, user_data):
        try:
            user_id = user_data.get('uid')
            if not user_id:
                return None    
            user_ref = self.db.collection(self.user_collection).document(user_id)
            existing_user = user_ref.get()
            
            if not existing_user.exists:
                user_data["role"] = user_data.get("role", "ADMIN")
                user_data["created_at"] = firestore.SERVER_TIMESTAMP
                user_data["created_by"] = user_data.get("created_by", None)
                user_data["last_login"] = firestore.SERVER_TIMESTAMP
                user_ref.set(user_data)
                return user_data
            else:
                user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
                return existing_user.to_dict()
        except Exception as e:
            print(f"❌ Error saving user: {e}")
            return None

    def get_user_by_id(self, user_id):
        """Gets a user document by their ID."""
        try:
            if not user_id:
                return None
            doc = self.db.collection(self.user_collection).document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None

    def get_my_sub_users(self, admin_id):
        try:
            docs = self.db.collection(self.user_collection)\
                .where(filter=FieldFilter('created_by', '==', admin_id)).stream()
            return [{**doc.to_dict(), 'uid': doc.id} for doc in docs]
        except Exception as e:
            print(f"❌ Error fetching sub-users: {e}")
            return []

    def get_published_count(self, user_id):
        try:
            count_query = self.db.collection(self.collection_name)\
                                .where(filter=FieldFilter('author_id', '==', user_id))\
                                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                                .count()
            count_result = count_query.get()
            return count_result[0][0].value
        except Exception as e:
            print(f"❌ Error getting published blogs count: {e}")
            return 0
        
        
        
    def update_blog_status(self, blog_id, new_status):
        try:
            doc_ref = self.db.collection("blogs").document(blog_id)

            doc_ref.update({
                "status": new_status,
                "updated_at": datetime.utcnow()
            })

            return True
        except Exception as e:
            print("Firestore Status Error:", e)
            return False
        
# Categories functions
    def get_category_by_id(self, category_id, user_id=None):
        try:
            doc_ref = self.db.collection("categories").document(category_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            if user_id and data.get("created_by") != user_id:
                return None  # Unauthorized access
            data["id"] = doc.id
            return data
        except Exception as e:
            print(f"❌ Error fetching category {category_id}: {e}")
            return None
        
        
    def get_blogs_by_category(self, category_id, user_id):
        try:
            # Fetch the category name
            cat = self.get_category_by_id(category_id, user_id)
            if not cat:
                return []

            category_name = cat.get("name")
            docs = self.db.collection("blogs")\
                .where(filter=FieldFilter("category", "==", category_name))\
                .where(filter=FieldFilter("author_id", "==", user_id))\
                .stream()

            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"❌ Error fetching blogs by category {category_id}: {e}")
            return []
        
        
    def update_category_name(self, category_id, new_name, user_id):
        try:
            doc_ref = self.db.collection("categories").document(category_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            data = doc.to_dict()
            if data.get("created_by") != user_id:
                return False  # unauthorized
            doc_ref.update({"name": new_name})

            # Invalidate category cache for this user
            cache.clear_prefix(f"categories:{user_id}")

            return True
        except Exception as e:
            print(f"❌ Error updating category name: {e}")
            return False

    def create_category(self, name, user_id):
        try:
            # Check if exists first
            existing = self.db.collection("categories")\
                .where(filter=FieldFilter("name", "==", name))\
                .where(filter=FieldFilter("created_by", "==", user_id)).limit(1).get()

            if len(existing) > 0:
                return False, "Category already exists"

            doc_ref = self.db.collection("categories").add({
                "name": name,
                "count": 0,
                "created_by": user_id,
                "created_at": firestore.SERVER_TIMESTAMP
            })

            # Invalidate category cache for this user
            cache.clear_prefix(f"categories:{user_id}")

            return True, doc_ref[1].id
        except Exception as e:
            print(f"❌ Error creating category: {e}")
            return False, str(e)

    # ---------------- OPTIMIZED BATCH METHODS ----------------

    def get_dashboard_data(self, user_id):
        """
        Fetch all dashboard data in parallel for better performance.
        Returns dict with all dashboard metrics.
        """
        from app.utils.parallel import run_parallel_simple

        try:
            # Define all queries to run in parallel
            queries = [
                (self.get_published_count, (user_id,)),
                (self.get_blogs_by_status, ("DRAFT", user_id)),
                (self.get_blogs_by_status, ("UNDER_REVIEW", user_id)),
                (self.get_total_blogs_count, (user_id,)),
                (self.get_all_categories, (user_id,)),
                (self.get_recent_activity, (user_id, 10)),
            ]

            # Run all queries in parallel
            results = run_parallel_simple(queries, max_workers=6)

            return {
                "published_count": results[0] or 0,
                "drafts": results[1] or [],
                "pending": results[2] or [],
                "total_blogs": results[3] or 0,
                "categories": results[4] or [],
                "recent_activity": results[5] or [],
            }
        except Exception as e:
            print(f"❌ Error fetching dashboard data: {e}")
            return {
                "published_count": 0,
                "drafts": [],
                "pending": [],
                "total_blogs": 0,
                "categories": [],
                "recent_activity": [],
            }

    # ---------------- SITE SETTINGS METHODS ----------------

    def _get_site_settings_defaults(self, user_id):
        """Returns the default site settings schema."""
        return {
            "id": user_id,
            "owner_id": user_id,
            # General
            "site_name": "My Blog",
            "site_description": "Welcome to my blog",
            "niche": "",
            # Appearance
            "logo_url": "",
            "favicon_url": "",
            "primary_color": "#4318FF",
            "cover_image_url": "",
            # Content
            "posts_per_page": 10,
            "default_language": "en",
            "show_reading_time": True,
            "show_author": True,
            "featured_post_id": "",
            # SEO
            "meta_title": "",
            "meta_description": "",
            "og_image_url": "",
            "analytics_id": "",
            # Social
            "social_links": {
                "twitter": "",
                "linkedin": "",
                "github": ""
            },
            "contact_email": "",
            "about_content": "",
            # Behavior
            "site_visibility": "public"
        }

    def get_site_settings(self, user_id):
        """
        Retrieves site settings for a user.
        Merges stored data with defaults to ensure all fields exist.
        """
        try:
            defaults = self._get_site_settings_defaults(user_id)
            doc = self.db.collection("site_settings").document(user_id).get()

            if doc.exists:
                stored_data = doc.to_dict()
                # Deep merge: defaults first, then stored data overwrites
                merged = {**defaults, **stored_data}
                merged['id'] = doc.id

                # Handle nested social_links merge
                default_social = defaults.get('social_links', {})
                stored_social = stored_data.get('social_links', {})
                merged['social_links'] = {**default_social, **stored_social}

                return merged

            return defaults
        except Exception as e:
            print(f"❌ Error fetching site settings: {e}")
            return self._get_site_settings_defaults(user_id)

    def _validate_site_settings(self, settings):
        """Validates and sanitizes site settings input."""
        validated = {}

        # String fields with max lengths
        string_fields = {
            'site_name': 100,
            'site_description': 500,
            'niche': 50,
            'logo_url': 500,
            'favicon_url': 500,
            'cover_image_url': 500,
            'default_language': 10,
            'featured_post_id': 100,
            'meta_title': 70,
            'meta_description': 160,
            'og_image_url': 500,
            'analytics_id': 50,
            'contact_email': 100,
            'about_content': 5000,
        }

        for field, max_len in string_fields.items():
            if field in settings:
                val = str(settings[field]).strip()[:max_len]
                validated[field] = val

        # Primary color validation (hex format)
        if 'primary_color' in settings:
            color = str(settings['primary_color']).strip()
            if color.startswith('#') and len(color) in [4, 7]:
                validated['primary_color'] = color
            else:
                validated['primary_color'] = '#4318FF'

        # Integer fields with bounds
        if 'posts_per_page' in settings:
            try:
                val = int(settings['posts_per_page'])
                validated['posts_per_page'] = max(1, min(50, val))
            except (ValueError, TypeError):
                validated['posts_per_page'] = 10

        # Boolean fields
        bool_fields = ['show_reading_time', 'show_author']
        for field in bool_fields:
            if field in settings:
                validated[field] = bool(settings[field])

        # Enum validation for site_visibility
        if 'site_visibility' in settings:
            vis = str(settings['site_visibility']).lower()
            validated['site_visibility'] = vis if vis in ['public', 'unlisted'] else 'public'

        # Social links (nested object)
        if 'social_links' in settings and isinstance(settings['social_links'], dict):
            validated['social_links'] = {
                'twitter': str(settings['social_links'].get('twitter', '')).strip()[:200],
                'linkedin': str(settings['social_links'].get('linkedin', '')).strip()[:200],
                'github': str(settings['social_links'].get('github', '')).strip()[:200],
            }

        return validated

    def update_site_settings(self, user_id, settings):
        """
        Updates or creates site settings for a user.
        Validates input before saving.
        """
        try:
            # Validate settings
            validated = self._validate_site_settings(settings)
            validated['owner_id'] = user_id
            validated['updated_at'] = datetime.utcnow()

            doc_ref = self.db.collection("site_settings").document(user_id)
            doc_ref.set(validated, merge=True)
            return True
        except Exception as e:
            print(f"❌ Error updating site settings: {e}")
            return False

    def get_published_blogs(self, user_id, limit=20):
        """
        Fetches published blogs for the public site.
        Returns blogs ordered by updated_at descending.
        """
        try:
            query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('author_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                .order_by('updated_at', direction=firestore.Query.DESCENDING)

            if limit:
                query = query.limit(limit)

            blogs = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                # Process content for display
                raw_content = data.get('content', '')
                if isinstance(raw_content, dict):
                    data['content'] = raw_content
                else:
                    data['content'] = {'body': str(raw_content) if raw_content else ''}
                blogs.append(data)
            return blogs
        except Exception as e:
            print(f"❌ Error fetching published blogs: {e}")
            return []

    def get_published_blog_by_id(self, blog_id):
        """
        Fetches a single published blog by ID.
        Returns None if blog doesn't exist or is not published.
        """
        try:
            doc = self.db.collection(self.collection_name).document(blog_id).get()
            if doc.exists:
                data = doc.to_dict()
                # Only return if published
                if data.get('status') != 'PUBLISHED':
                    return None
                data['id'] = doc.id
                # Process content for display
                raw_content = data.get('content', '')
                if isinstance(raw_content, dict):
                    data['content'] = raw_content
                else:
                    data['content'] = {'body': str(raw_content) if raw_content else ''}
                return data
            return None
        except Exception as e:
            print(f"❌ Error fetching published blog {blog_id}: {e}")
            return None

    # ---------------- CONTACT & NEWSLETTER METHODS ----------------

    def save_contact_submission(self, user_id, data):
        """
        Saves a contact form submission to Firestore.
        Stores in 'contact_submissions' collection.
        """
        try:
            submission = {
                'site_owner_id': user_id,
                'name': data.get('name', '').strip()[:100],
                'email': data.get('email', '').strip()[:100],
                'subject': data.get('subject', '').strip()[:200],
                'message': data.get('message', '').strip()[:5000],
                'created_at': firestore.SERVER_TIMESTAMP,
                'read': False
            }
            doc_ref = self.db.collection('contact_submissions').add(submission)
            return doc_ref[1].id
        except Exception as e:
            print(f"❌ Error saving contact submission: {e}")
            return None

    def save_newsletter_subscriber(self, user_id, email):
        """
        Saves a newsletter subscriber to Firestore.
        Uses email as part of doc ID to prevent duplicates.
        """
        try:
            email_clean = email.strip().lower()
            subscriber = {
                'site_owner_id': user_id,
                'email': email_clean,
                'subscribed_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            # Create unique doc ID to prevent duplicates
            doc_id = f"{user_id}_{email_clean.replace('@', '_at_').replace('.', '_')}"
            self.db.collection('newsletter_subscribers').document(doc_id).set(subscriber, merge=True)
            return doc_id
        except Exception as e:
            print(f"❌ Error saving newsletter subscriber: {e}")
            return None

    def get_contact_submissions(self, user_id, limit=50):
        """
        Fetches contact submissions for a site owner.
        """
        try:
            docs = self.db.collection('contact_submissions')\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()

            submissions = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                submissions.append(data)
            return submissions
        except Exception as e:
            print(f"❌ Error fetching contact submissions: {e}")
            return []

    def get_newsletter_subscribers(self, user_id, limit=100):
        """
        Fetches newsletter subscribers for a site owner.
        """
        try:
            docs = self.db.collection('newsletter_subscribers')\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('active', '==', True))\
                .order_by('subscribed_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()

            subscribers = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                subscribers.append(data)
            return subscribers
        except Exception as e:
            print(f"❌ Error fetching newsletter subscribers: {e}")
            return []