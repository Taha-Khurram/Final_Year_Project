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
        """Saves blog as DRAFT, increments category count, and generates unique slug."""
        try:
            from app.utils.slug_utils import generate_slug, ensure_unique_slug

            blog_data['created_at'] = firestore.SERVER_TIMESTAMP
            blog_data['updated_at'] = datetime.utcnow()
            blog_data['author_id'] = user_id
            blog_data['site_owner_id'] = self.get_site_owner_for_user(user_id)
            blog_data['status'] = blog_data.get('status', 'DRAFT').upper()

            # Generate unique slug from title
            site_owner = blog_data['site_owner_id']
            title = blog_data.get('title', 'Untitled')
            base_slug = generate_slug(title)
            existing_slugs = self._get_user_slugs(site_owner)
            blog_data['slug'] = ensure_unique_slug(base_slug, existing_slugs)
            blog_data['old_slugs'] = []
            blog_data['numeric_id'] = self._get_next_numeric_id(site_owner)

            doc_ref = self.db.collection(self.collection_name).add(blog_data)
            blog_id = doc_ref[1].id

            # Use site_owner_id for category management
            category_name = blog_data.get('category')
            if category_name:
                self.update_category_count(category_name, 1, site_owner)

            return blog_id
        except Exception as e:
            print(f"❌ Firestore Error creating draft: {e}")
            return None

    def update_blog_content(self, blog_id, title, content, new_slug=None, seo_title=None, seo_description=None):
        """
        Updates the title and body content of a blog post.
        If new_slug is provided and different from current, updates slug and tracks old one.
        If title changes and no new_slug provided, auto-generates new slug from title.
        Also handles SEO meta title and description fields.
        """
        try:
            from app.utils.slug_utils import generate_slug, ensure_unique_slug

            doc_ref = self.db.collection(self.collection_name).document(blog_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            current_data = doc.to_dict()
            current_slug = current_data.get('slug', '')
            current_title = current_data.get('title', '')

            update_data = {
                'title': title,
                'content': content,
                'updated_at': datetime.utcnow()
            }

            # Update SEO fields if provided
            if seo_title is not None:
                update_data['seo_title'] = seo_title
            if seo_description is not None:
                update_data['seo_description'] = seo_description

            # Determine slug to use
            slug_to_set = new_slug

            # If no explicit slug provided and title changed, auto-generate new slug
            if not slug_to_set and title != current_title:
                base_slug = generate_slug(title)
                user_id = current_data.get('site_owner_id') or current_data.get('author_id')
                if user_id:
                    existing_slugs = self._get_user_slugs(user_id)
                    # Remove current slug from existing to allow keeping it
                    existing_slugs.discard(current_slug)
                    slug_to_set = ensure_unique_slug(base_slug, existing_slugs)
                else:
                    slug_to_set = base_slug

            # Update slug if we have a new one different from current
            if slug_to_set and slug_to_set != current_slug:
                # Store old slug for 301 redirects
                old_slugs = current_data.get('old_slugs', [])
                if current_slug and current_slug not in old_slugs:
                    old_slugs.append(current_slug)
                # Keep only last 10 old slugs
                update_data['old_slugs'] = old_slugs[-10:]
                update_data['slug'] = slug_to_set

            doc_ref.update(update_data)
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

    def get_site_owner_for_user(self, user_id):
        """
        Gets the site owner for a user.
        - If user is an ADMIN or has no created_by, they are their own site owner
        - If user was created by an admin, that admin is the site owner
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return user_id  # Fallback to self

            # If user is admin or wasn't created by anyone, they own their own site
            if user.get('role') == 'ADMIN' or not user.get('created_by'):
                return user_id

            # Return the admin who created this user
            return user.get('created_by')
        except Exception as e:
            print(f"❌ Error getting site owner: {e}")
            return user_id  # Fallback to self

    def get_published_count(self, user_id):
        """Get count of published blogs for a site owner (includes team members' blogs)."""
        try:
            # Count by site_owner_id
            count_query = self.db.collection(self.collection_name)\
                                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                                .count()
            count_result = count_query.get()
            site_owner_count = count_result[0][0].value

            # Also count by author_id for backwards compatibility (older blogs)
            fallback_query = self.db.collection(self.collection_name)\
                                .where(filter=FieldFilter('author_id', '==', user_id))\
                                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                                .count()
            fallback_result = fallback_query.get()
            author_count = fallback_result[0][0].value

            # Return max to avoid double counting (site_owner_id blogs are also author_id blogs for admins)
            return max(site_owner_count, author_count)
        except Exception as e:
            print(f"❌ Error getting published blogs count: {e}")
            return 0
        
        
        
    def update_blog_status(self, blog_id, new_status):
        """Updates blog status and invalidates published blogs cache."""
        try:
            doc_ref = self.db.collection("blogs").document(blog_id)

            # Get blog to find site_owner_id for cache invalidation
            doc = doc_ref.get()
            site_owner_id = None
            if doc.exists:
                data = doc.to_dict()
                site_owner_id = data.get('site_owner_id') or data.get('author_id')

            doc_ref.update({
                "status": new_status,
                "updated_at": datetime.utcnow()
            })

            # Invalidate published blogs cache for this site owner
            if site_owner_id:
                cache.clear_prefix(f"published_blogs:{site_owner_id}")

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

    # ---------------- APP SETTINGS METHODS ----------------

    def _get_app_settings_defaults(self):
        """Returns default app-level settings schema."""
        return {
            "app_name": "Scriptly",
            "tagline": "Create, Manage & Publish Beautiful Blogs",
            "app_logo": "",
            "app_favicon": "",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    def get_app_settings(self):
        """Fetches app-level settings from Firestore."""
        try:
            cache_key = "app_settings"
            cached = cache.get(cache_key)
            if cached:
                return cached

            doc = self.db.collection("app_config").document("general").get()
            defaults = self._get_app_settings_defaults()

            if doc.exists:
                stored_data = doc.to_dict()
                merged = {**defaults, **stored_data}
                cache.set(cache_key, merged, ttl=300)
                return merged

            # Initialize with defaults if not exists
            self.db.collection("app_config").document("general").set(defaults)
            cache.set(cache_key, defaults, ttl=300)
            return defaults

        except Exception as e:
            print(f"❌ Error fetching app settings: {e}")
            return self._get_app_settings_defaults()

    def update_app_settings(self, settings_data):
        """Updates app-level settings in Firestore."""
        try:
            settings_data['updated_at'] = datetime.utcnow()

            self.db.collection("app_config").document("general").set(
                settings_data,
                merge=True
            )

            # Clear cache
            cache.delete("app_settings")

            return True
        except Exception as e:
            print(f"❌ Error updating app settings: {e}")
            return False

    # ---------------- SITE SETTINGS METHODS ----------------

    def _get_site_settings_defaults(self, user_id):
        """Returns the default site settings schema."""
        return {
            "id": user_id,
            "owner_id": user_id,
            "site_slug": "",  # URL-friendly slug for clean URLs (e.g., 'my-blog' -> /site/my-blog)
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
            "site_visibility": "public",
            # Locale & Timezone
            "timezone": "UTC",
            "date_format": "MMM DD, YYYY",
            "time_format": "12h",
            "locale": "en",
            # Header Settings
            "header": {
                "nav_home": "Home",
                "nav_blog": "Blog",
                "nav_about": "About",
                "nav_contact": "Contact",
                "cta_text": "Subscribe",
                "show_search": True
            },
            # Footer Settings
            "footer": {
                "copyright": "2024 {site_name}. All rights reserved.",
                "col1_title": "Navigation",
                "col2_title": "Support",
                "col3_title": "Legal & Social",
                "show_newsletter": True,
                "newsletter_title": "Stay Updated",
                "newsletter_description": "Get the latest posts delivered to your inbox."
            },
            # Hero Sections
            "hero_home": {
                "badge": "{niche}",
                "title": "Welcome to {site_name}",
                "subtitle": "{site_description}",
                "cta_primary": "Explore Articles",
                "cta_secondary": "Learn More",
                "stats_label_1": "Articles",
                "stats_label_2": "Categories",
                "stats_label_3": "Readers"
            },
            "hero_about": {
                "title": "About {site_name}",
                "subtitle": "{site_description}",
                "story_title": "Our Story",
                "values_title": "What We Stand For",
                "value_1_title": "Quality Content",
                "value_1_desc": "Every article is crafted with care and attention to detail.",
                "value_2_title": "Community First",
                "value_2_desc": "We believe in building meaningful connections.",
                "value_3_title": "Authenticity",
                "value_3_desc": "Real experiences, honest opinions, genuine insights.",
                "stats_title": "By the Numbers",
                "cta_title": "Ready to Explore?",
                "cta_subtitle": "Dive into our articles and join the conversation."
            },
            "hero_blog": {
                "title": "Our Blog",
                "subtitle": "Explore our collection of articles, guides, and insights."
            },
            "hero_contact": {
                "title": "Get in Touch",
                "subtitle": "Have questions or feedback? We would love to hear from you.",
                "form_title": "Send a Message",
                "form_subtitle": "Fill out the form and we will get back to you.",
                "faq_1_q": "How quickly do you respond?",
                "faq_1_a": "We typically respond within 24-48 hours.",
                "faq_2_q": "Can I contribute articles?",
                "faq_2_a": "Yes! We welcome guest contributions.",
                "faq_3_q": "Do you offer sponsorships?",
                "faq_3_a": "Contact us to discuss partnership opportunities.",
                "faq_4_q": "How do I report an issue?",
                "faq_4_a": "Use the contact form or email us directly."
            },

            # Permalink settings
            "permalinks": {
                "structure": "post-name",     # post-name, date-post-name, category-post-name, numeric
                "category_base": "category",  # URL base for categories (e.g., /category/tech)
                "tag_base": "tag",            # URL base for tags (e.g., /tag/python)
            },

            # SEO & Search Visibility
            "seo": {
                "indexing_enabled": True,     # Enable/disable search engine indexing
                "robots_txt_custom": "",      # Custom robots.txt content (if empty, auto-generate)
                "og_site_name": "",           # Open Graph site name
                "og_default_image": "",       # Default OG image for posts without cover
                "twitter_card": "summary_large_image",  # summary, summary_large_image
                "twitter_site": "",           # @username for site
                "google_site_verification": "",  # Google Search Console verification
                "bing_site_verification": "",    # Bing Webmaster verification
            },

            # RSS Feed Settings
            "rss": {
                "enabled": True,              # Enable/disable RSS feed
                "posts_count": 20,            # Number of posts in feed
                "content_type": "summary",    # 'full' or 'summary'
                "include_featured_image": True,  # Include cover images in feed
            },

            # Legal Pages & Cookie Consent
            "legal": {
                "contact_email": "",  # Specific email for legal pages, falls back to main contact_email
                "privacy_policy_enabled": True,
                "privacy_policy_content": """## Privacy Policy

**Last updated: {date}**

### Introduction
Welcome to {site_name}. We respect your privacy and are committed to protecting your personal data.

### Information We Collect
We may collect information you provide directly, including:
- Name and email address when you subscribe to our newsletter
- Contact information when you reach out via our contact form
- Comments and feedback you submit

### How We Use Your Information
We use the information we collect to:
- Send you newsletters and updates (if subscribed)
- Respond to your inquiries
- Improve our content and services

### Cookies
We use cookies to enhance your browsing experience. You can control cookie preferences through your browser settings.

### Third-Party Services
We may use third-party services like Google Analytics to understand how visitors use our site.

### Your Rights
You have the right to:
- Access your personal data
- Request correction of your data
- Request deletion of your data
- Unsubscribe from communications

### Contact Us
If you have questions about this Privacy Policy, please contact us at {contact_email}.
""",
                "terms_of_service_enabled": True,
                "terms_of_service_content": """## Terms of Service

**Last updated: {date}**

### Agreement to Terms
By accessing {site_name}, you agree to be bound by these Terms of Service.

### Intellectual Property
All content on this site, including text, images, and graphics, is owned by {site_name} and protected by copyright laws.

### User Conduct
You agree not to:
- Use the site for any unlawful purpose
- Attempt to gain unauthorized access
- Interfere with the site's operation
- Copy or reproduce content without permission

### Comments and Submissions
By submitting comments or content, you grant us a non-exclusive license to use, modify, and display that content.

### Disclaimer
The content on this site is provided "as is" without warranties of any kind. We do not guarantee the accuracy or completeness of any information.

### Limitation of Liability
{site_name} shall not be liable for any damages arising from your use of this site.

### Changes to Terms
We reserve the right to modify these terms at any time. Continued use of the site constitutes acceptance of updated terms.

### Contact
For questions about these Terms, contact us at {contact_email}.
""",
                "cookie_consent_enabled": True,
                "cookie_consent_text": "We use cookies to enhance your browsing experience and analyze site traffic.",
                "cookie_consent_button": "Accept",
                "cookie_consent_link_text": "Learn more",
            }
        }

    def get_site_settings(self, user_id):
        """
        Retrieves site settings for a user.
        Merges stored data with defaults to ensure all fields exist.
        Uses in-memory cache with 2-minute TTL to reduce Firestore queries.
        """
        cache_key = f"site_settings:{user_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            defaults = self._get_site_settings_defaults(user_id)
            doc = self.db.collection("site_settings").document(user_id).get()

            if doc.exists:
                stored_data = doc.to_dict()
                # Deep merge: defaults first, then stored data overwrites
                merged = {**defaults, **stored_data}
                merged['id'] = doc.id

                # Handle nested object merges
                nested_fields = ['social_links', 'header', 'footer',
                               'hero_home', 'hero_about', 'hero_blog', 'hero_contact', 'permalinks', 'seo', 'rss', 'legal']
                for field in nested_fields:
                    default_obj = defaults.get(field, {})
                    stored_obj = stored_data.get(field, {})
                    merged[field] = {**default_obj, **stored_obj}

                cache.set(cache_key, merged, ttl=120)
                return merged

            cache.set(cache_key, defaults, ttl=120)
            return defaults
        except Exception as e:
            print(f"❌ Error fetching site settings: {e}")
            return self._get_site_settings_defaults(user_id)

    def resolve_site_identifier(self, identifier):
        """
        Resolves a site identifier (slug or user_id) to the actual user_id.
        Returns tuple: (user_id, settings) or (None, None) if not found.
        Supports both clean slug URLs and legacy user_id URLs for backwards compatibility.
        """
        try:
            # Check cache first for slug resolution
            cache_key = f"slug_resolve:{identifier}"
            cached = cache.get(cache_key)
            if cached:
                return cached, self.get_site_settings(cached)

            # Try direct user_id lookup first (for backwards compatibility)
            doc = self.db.collection("site_settings").document(identifier).get()
            if doc.exists:
                cache.set(cache_key, identifier, ttl=300)
                return identifier, self.get_site_settings(identifier)

            # Try slug lookup
            query = self.db.collection("site_settings").where(
                filter=FieldFilter('site_slug', '==', identifier)
            ).limit(1)
            docs = list(query.stream())

            if docs:
                user_id = docs[0].id
                cache.set(cache_key, user_id, ttl=300)
                return user_id, self.get_site_settings(user_id)

            return None, None

        except Exception as e:
            print(f"❌ Error resolving site identifier: {e}")
            return None, None

    def is_slug_available(self, slug, exclude_user_id=None):
        """
        Check if a site slug is available.
        Returns True if available, False if taken.
        """
        try:
            if not slug:
                return False

            query = self.db.collection("site_settings").where(
                filter=FieldFilter('site_slug', '==', slug)
            ).limit(1)
            docs = list(query.stream())

            if not docs:
                return True

            # If excluding a user (for updates), check if the found doc belongs to them
            if exclude_user_id and docs[0].id == exclude_user_id:
                return True

            return False

        except Exception as e:
            print(f"❌ Error checking slug availability: {e}")
            return False

    def generate_unique_site_slug(self, base_slug, exclude_user_id=None):
        """
        Generate a unique site slug from a base slug.
        Appends numbers if slug is taken: my-blog -> my-blog-2 -> my-blog-3
        """
        from app.utils.slug_utils import generate_slug

        # Clean the base slug
        slug = generate_slug(base_slug)
        if not slug:
            slug = "my-site"

        # Check if available
        if self.is_slug_available(slug, exclude_user_id):
            return slug

        # Try with numbers
        counter = 2
        while counter < 100:  # Reasonable limit
            new_slug = f"{slug}-{counter}"
            if self.is_slug_available(new_slug, exclude_user_id):
                return new_slug
            counter += 1

        # Fallback to timestamp-based slug
        import time
        return f"{slug}-{int(time.time())}"

    def _validate_site_settings(self, settings):
        """Validates and sanitizes site settings input."""
        validated = {}

        # String fields with max lengths
        string_fields = {
            'site_name': 100,
            'site_slug': 50,
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
            'timezone': 50,
            'date_format': 20,
            'time_format': 5,
            'locale': 10,
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

        # Header settings (nested object)
        if 'header' in settings and isinstance(settings['header'], dict):
            h = settings['header']
            validated['header'] = {
                'nav_home': str(h.get('nav_home', 'Home')).strip()[:50],
                'nav_blog': str(h.get('nav_blog', 'Blog')).strip()[:50],
                'nav_about': str(h.get('nav_about', 'About')).strip()[:50],
                'nav_contact': str(h.get('nav_contact', 'Contact')).strip()[:50],
                'cta_text': str(h.get('cta_text', 'Subscribe')).strip()[:50],
                'show_search': bool(h.get('show_search', True)),
            }

        # Footer settings (nested object)
        if 'footer' in settings and isinstance(settings['footer'], dict):
            f = settings['footer']
            validated['footer'] = {
                'copyright': str(f.get('copyright', '')).strip()[:200],
                'col1_title': str(f.get('col1_title', 'Navigation')).strip()[:50],
                'col2_title': str(f.get('col2_title', 'Support')).strip()[:50],
                'col3_title': str(f.get('col3_title', 'Legal & Social')).strip()[:50],
                'show_newsletter': bool(f.get('show_newsletter', True)),
                'newsletter_title': str(f.get('newsletter_title', '')).strip()[:100],
                'newsletter_description': str(f.get('newsletter_description', '')).strip()[:300],
            }

        # Hero sections (nested objects)
        hero_sections = ['hero_home', 'hero_about', 'hero_blog', 'hero_contact']
        for section in hero_sections:
            if section in settings and isinstance(settings[section], dict):
                validated[section] = {}
                for key, val in settings[section].items():
                    if isinstance(val, str):
                        validated[section][key] = val.strip()[:500]
                    elif isinstance(val, bool):
                        validated[section][key] = val

        # Permalink settings (nested object)
        if 'permalinks' in settings and isinstance(settings['permalinks'], dict):
            p = settings['permalinks']
            valid_structures = ['post-name', 'date-post-name', 'category-post-name', 'numeric']
            structure = str(p.get('structure', 'post-name')).strip().lower()
            validated['permalinks'] = {
                'structure': structure if structure in valid_structures else 'post-name',
                'category_base': str(p.get('category_base', 'category')).strip().lower()[:50],
                'tag_base': str(p.get('tag_base', 'tag')).strip().lower()[:50],
            }
            # Sanitize URL bases (only alphanumeric and hyphens)
            import re
            validated['permalinks']['category_base'] = re.sub(r'[^a-z0-9-]', '', validated['permalinks']['category_base']) or 'category'
            validated['permalinks']['tag_base'] = re.sub(r'[^a-z0-9-]', '', validated['permalinks']['tag_base']) or 'tag'

        # SEO settings (nested object)
        if 'seo' in settings and isinstance(settings['seo'], dict):
            s = settings['seo']
            valid_twitter_cards = ['summary', 'summary_large_image']
            twitter_card = str(s.get('twitter_card', 'summary_large_image')).strip().lower()
            validated['seo'] = {
                'indexing_enabled': bool(s.get('indexing_enabled', True)),
                'robots_txt_custom': str(s.get('robots_txt_custom', '')).strip()[:2000],
                'og_site_name': str(s.get('og_site_name', '')).strip()[:100],
                'og_default_image': str(s.get('og_default_image', '')).strip()[:500],
                'twitter_card': twitter_card if twitter_card in valid_twitter_cards else 'summary_large_image',
                'twitter_site': str(s.get('twitter_site', '')).strip()[:50],
                'google_site_verification': str(s.get('google_site_verification', '')).strip()[:100],
                'bing_site_verification': str(s.get('bing_site_verification', '')).strip()[:100],
            }

        return validated

    def update_site_settings(self, user_id, settings):
        """
        Updates or creates site settings for a user.
        Validates input before saving. Invalidates cache on update.
        """
        try:
            # Validate settings
            validated = self._validate_site_settings(settings)
            validated['owner_id'] = user_id
            validated['updated_at'] = datetime.utcnow()

            doc_ref = self.db.collection("site_settings").document(user_id)
            doc_ref.set(validated, merge=True)

            # Invalidate cached settings
            cache.delete(f"site_settings:{user_id}")
            return True
        except Exception as e:
            print(f"❌ Error updating site settings: {e}")
            return False

    def get_published_blogs(self, user_id, limit=20):
        """
        Fetches published blogs for the public site.
        Returns blogs ordered by updated_at descending.
        Filters by site_owner_id to include blogs from all team members.
        Falls back to author_id for backwards compatibility with older blogs.
        Uses in-memory cache with 2-minute TTL to reduce Firestore queries.
        Auto-generates slugs for existing blogs that don't have them.
        """
        cache_key = f"published_blogs:{user_id}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            blogs = []
            blog_ids = set()

            # Fetch by site_owner_id (no order_by to avoid composite index)
            site_owner_query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))

            for doc in site_owner_query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                blog_ids.add(doc.id)
                # Process content for display
                raw_content = data.get('content', '')
                if isinstance(raw_content, dict):
                    data['content'] = raw_content
                else:
                    data['content'] = {'body': str(raw_content) if raw_content else ''}
                # Ensure slug exists (auto-migrate if needed)
                data = self._ensure_blog_slug(data, doc.id)
                blogs.append(data)

            # Fallback: also fetch by author_id for older blogs without site_owner_id
            fallback_query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('author_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))

            for doc in fallback_query.stream():
                if doc.id not in blog_ids:  # Avoid duplicates
                    data = doc.to_dict()
                    data['id'] = doc.id
                    raw_content = data.get('content', '')
                    if isinstance(raw_content, dict):
                        data['content'] = raw_content
                    else:
                        data['content'] = {'body': str(raw_content) if raw_content else ''}
                    # Ensure slug exists (auto-migrate if needed)
                    data = self._ensure_blog_slug(data, doc.id)
                    blogs.append(data)

            # Sort combined results by updated_at in Python (newest first)
            blogs.sort(key=lambda x: x.get('updated_at', datetime.min), reverse=True)

            result = blogs[:limit] if limit else blogs
            cache.set(cache_key, result, ttl=120)
            return result
        except Exception as e:
            print(f"❌ Error fetching published blogs: {e}")
            return []

    def get_published_blog_by_id(self, blog_id):
        """
        Fetches a single published blog by ID.
        Returns None if blog doesn't exist or is not published.
        Auto-generates slug if missing.
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
                # Ensure slug exists (auto-migrate if needed)
                data = self._ensure_blog_slug(data, doc.id)
                return data
            return None
        except Exception as e:
            print(f"❌ Error fetching published blog {blog_id}: {e}")
            return None

    def get_published_blog_by_slug(self, user_id, slug):
        """
        Fetches a published blog by slug.
        Also checks old_slugs for 301 redirect handling.
        Returns dict with 'blog', 'redirect' (bool), and 'new_slug' (if redirect).
        """
        try:
            # Try current slug first
            query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('slug', '==', slug))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                .limit(1)
            docs = list(query.stream())
            if docs:
                data = docs[0].to_dict()
                data['id'] = docs[0].id
                # Process content for display
                raw_content = data.get('content', '')
                if isinstance(raw_content, dict):
                    data['content'] = raw_content
                else:
                    data['content'] = {'body': str(raw_content) if raw_content else ''}
                return {'blog': data, 'redirect': False}

            # Check old_slugs for 301 redirect
            query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('old_slugs', 'array_contains', slug))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))\
                .limit(1)
            docs = list(query.stream())
            if docs:
                data = docs[0].to_dict()
                data['id'] = docs[0].id
                # Process content for display
                raw_content = data.get('content', '')
                if isinstance(raw_content, dict):
                    data['content'] = raw_content
                else:
                    data['content'] = {'body': str(raw_content) if raw_content else ''}
                return {'blog': data, 'redirect': True, 'new_slug': data.get('slug')}

            return None
        except Exception as e:
            print(f"❌ Error fetching blog by slug {slug}: {e}")
            return None

    def _get_user_slugs(self, user_id):
        """
        Gets all existing slugs for a user's blogs (for uniqueness check).
        Returns a set of slugs.
        """
        try:
            slugs = set()
            query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .select(['slug'])
            for doc in query.stream():
                data = doc.to_dict()
                if data.get('slug'):
                    slugs.add(data['slug'])
            return slugs
        except Exception as e:
            print(f"❌ Error fetching user slugs: {e}")
            return set()

    def _get_next_numeric_id(self, user_id):
        """
        Gets the next numeric ID for a user's blogs (for numeric permalink structure).
        Returns the next available integer ID.
        """
        try:
            query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .order_by('numeric_id', direction=firestore.Query.DESCENDING)\
                .limit(1)
            docs = list(query.stream())
            if docs:
                data = docs[0].to_dict()
                return (data.get('numeric_id') or 0) + 1
            return 1
        except Exception as e:
            # If query fails (e.g., no index), fallback to count
            try:
                count = len(list(self.db.collection(self.collection_name)
                    .where(filter=FieldFilter('site_owner_id', '==', user_id))
                    .select([]).stream()))
                return count + 1
            except:
                return 1

    def _ensure_blog_slug(self, blog_data, blog_id):
        """
        Ensures a blog has a slug. If not, generates one from the title and saves it.
        This handles migration of existing blogs that don't have slugs.
        Returns the blog data with slug guaranteed to be set.
        """
        if blog_data.get('slug'):
            return blog_data

        try:
            from app.utils.slug_utils import generate_slug, ensure_unique_slug

            title = blog_data.get('title', 'Untitled')
            base_slug = generate_slug(title)

            # Get existing slugs for this user
            user_id = blog_data.get('site_owner_id') or blog_data.get('author_id')
            if user_id:
                existing_slugs = self._get_user_slugs(user_id)
                slug = ensure_unique_slug(base_slug, existing_slugs)
            else:
                slug = base_slug

            # Save the slug to the database
            self.db.collection(self.collection_name).document(blog_id).update({
                'slug': slug,
                'old_slugs': []
            })

            blog_data['slug'] = slug
            blog_data['old_slugs'] = []

        except Exception as e:
            print(f"❌ Error ensuring blog slug for {blog_id}: {e}")
            # Fallback: use the document ID as slug
            blog_data['slug'] = blog_id

        return blog_data

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
        Returns tuple: (doc_id, is_new_subscriber)
        """
        try:
            email_clean = email.strip().lower()
            # Create unique doc ID to prevent duplicates
            doc_id = f"{user_id}_{email_clean.replace('@', '_at_').replace('.', '_')}"

            # Check if subscriber already exists
            doc_ref = self.db.collection('newsletter_subscribers').document(doc_id)
            existing_doc = doc_ref.get()

            if existing_doc.exists:
                existing_data = existing_doc.to_dict()
                # If already active subscriber, return as existing
                if existing_data.get('active', False):
                    return (doc_id, False)  # Already subscribed
                # If was unsubscribed, resubscribe them
                doc_ref.update({
                    'active': True,
                    'resubscribed_at': firestore.SERVER_TIMESTAMP
                })
                return (doc_id, True)  # Resubscribed

            # New subscriber
            subscriber = {
                'site_owner_id': user_id,
                'email': email_clean,
                'subscribed_at': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            doc_ref.set(subscriber)
            return (doc_id, True)  # New subscriber
        except Exception as e:
            print(f"❌ Error saving newsletter subscriber: {e}")
            return (None, False)

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
            # Simple query without order_by to avoid composite index requirement
            docs = self.db.collection('newsletter_subscribers')\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('active', '==', True))\
                .limit(limit)\
                .stream()

            subscribers = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                # Convert timestamp to ISO string for JSON serialization
                if data.get('subscribed_at'):
                    data['subscribed_at'] = data['subscribed_at'].isoformat()
                subscribers.append(data)

            # Sort by subscribed_at in Python (newest first)
            subscribers.sort(
                key=lambda x: x.get('subscribed_at') or '',
                reverse=True
            )
            return subscribers
        except Exception as e:
            print(f"❌ Error fetching newsletter subscribers: {e}")
            return []

    def get_subscriber_count(self, user_id):
        """Get total count of active subscribers."""
        try:
            count_query = self.db.collection('newsletter_subscribers')\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('active', '==', True))\
                .count()
            result = count_query.get()
            return result[0][0].value
        except Exception as e:
            print(f"❌ Error counting subscribers: {e}")
            return 0

    def unsubscribe_newsletter(self, user_id, email):
        """Mark subscriber as inactive (unsubscribed)."""
        try:
            email_clean = email.strip().lower()
            doc_id = f"{user_id}_{email_clean.replace('@', '_at_').replace('.', '_')}"
            doc_ref = self.db.collection('newsletter_subscribers').document(doc_id)

            doc = doc_ref.get()
            if not doc.exists:
                return False

            doc_ref.update({
                'active': False,
                'unsubscribed_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"❌ Error unsubscribing: {e}")
            return False

    def resubscribe_newsletter(self, user_id, email):
        """Reactivate a previously unsubscribed email."""
        try:
            email_clean = email.strip().lower()
            doc_id = f"{user_id}_{email_clean.replace('@', '_at_').replace('.', '_')}"
            doc_ref = self.db.collection('newsletter_subscribers').document(doc_id)

            doc = doc_ref.get()
            if not doc.exists:
                return False

            doc_ref.update({
                'active': True,
                'resubscribed_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"❌ Error resubscribing: {e}")
            return False

    def log_newsletter_send(self, user_id, recipient_count, subject, content_preview="", html_content=""):
        """Log a newsletter send for history tracking."""
        try:
            self.db.collection('newsletter_history').add({
                'user_id': user_id,
                'recipient_count': recipient_count,
                'subject': subject,
                'content_preview': content_preview[:500],
                'html_content': html_content,
                'sent_at': firestore.SERVER_TIMESTAMP,
                'status': 'sent'
            })
            return True
        except Exception as e:
            print(f"❌ Error logging newsletter: {e}")
            return False

    def get_newsletter_history(self, user_id, limit=20):
        """Get newsletter send history."""
        try:
            # Simple query without order_by to avoid composite index requirement
            docs = self.db.collection('newsletter_history')\
                .where(filter=FieldFilter('user_id', '==', user_id))\
                .limit(limit)\
                .stream()

            history = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                # Convert timestamp to ISO string for JSON serialization
                if data.get('sent_at'):
                    data['sent_at'] = data['sent_at'].isoformat()
                history.append(data)

            # Sort by sent_at in Python (newest first)
            history.sort(
                key=lambda x: x.get('sent_at') or '',
                reverse=True
            )
            return history
        except Exception as e:
            print(f"❌ Error fetching newsletter history: {e}")
            return []

    def get_newsletter_by_id(self, newsletter_id, user_id):
        """Get a single newsletter by ID."""
        try:
            doc = self.db.collection('newsletter_history').document(newsletter_id).get()
            if not doc.exists:
                return None
            data = doc.to_dict()
            # Verify ownership
            if data.get('user_id') != user_id:
                return None
            data['id'] = doc.id
            # Convert timestamp to ISO string for JSON serialization
            if data.get('sent_at'):
                data['sent_at'] = data['sent_at'].isoformat()
            return data
        except Exception as e:
            print(f"❌ Error fetching newsletter by ID: {e}")
            return None

    def delete_newsletter(self, newsletter_id, user_id):
        """Delete a newsletter from history."""
        try:
            doc_ref = self.db.collection('newsletter_history').document(newsletter_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            # Verify ownership
            if doc.to_dict().get('user_id') != user_id:
                return False
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"❌ Error deleting newsletter: {e}")
            return False

    def save_newsletter_draft(self, user_id, draft_data):
        """Save a newsletter draft for later editing."""
        try:
            draft = {
                'user_id': user_id,
                'subject': draft_data.get('subject', ''),
                'intro': draft_data.get('intro', ''),
                'posts': draft_data.get('posts', []),
                'cta_text': draft_data.get('cta_text', 'Read More'),
                'closing': draft_data.get('closing', ''),
                'html_content': draft_data.get('html_content', ''),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': datetime.utcnow(),
                'status': 'draft'
            }
            doc_ref = self.db.collection('newsletter_drafts').add(draft)
            return doc_ref[1].id
        except Exception as e:
            print(f"❌ Error saving newsletter draft: {e}")
            return None

    def get_newsletter_drafts(self, user_id, limit=10):
        """Get newsletter drafts."""
        try:
            # Simple query without order_by to avoid composite index requirement
            docs = self.db.collection('newsletter_drafts')\
                .where(filter=FieldFilter('user_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'draft'))\
                .limit(limit)\
                .stream()

            drafts = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                drafts.append(data)

            # Sort by updated_at in Python (newest first)
            drafts.sort(
                key=lambda x: x.get('updated_at') or '',
                reverse=True
            )
            return drafts
        except Exception as e:
            print(f"❌ Error fetching newsletter drafts: {e}")
            return []

    def delete_newsletter_draft(self, draft_id, user_id):
        """Delete a newsletter draft."""
        try:
            doc_ref = self.db.collection('newsletter_drafts').document(draft_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            if doc.to_dict().get('user_id') != user_id:
                return False
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"❌ Error deleting newsletter draft: {e}")
            return False

    # ---------------- EMBEDDING METHODS ----------------

    def update_blog_embedding(self, blog_id, embedding):
        """
        Store embedding vector for a blog post.
        Called when blog is published or updated.
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(blog_id)
            doc_ref.update({
                'embedding': embedding,
                'embedding_updated_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"❌ Error storing embedding: {e}")
            return False

    def get_blogs_with_embeddings(self, user_id, limit=100):
        """
        Fetch published blogs that have embeddings stored.
        Returns blogs with embedding vectors for semantic search.
        """
        try:
            blogs = []
            blog_ids = set()

            # Query by site_owner_id
            site_owner_query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))

            for doc in site_owner_query.stream():
                data = doc.to_dict()
                # Only include blogs with embeddings
                if data.get('embedding'):
                    data['id'] = doc.id
                    blog_ids.add(doc.id)
                    blogs.append(data)

            # Fallback: also fetch by author_id for older blogs
            fallback_query = self.db.collection(self.collection_name)\
                .where(filter=FieldFilter('author_id', '==', user_id))\
                .where(filter=FieldFilter('status', '==', 'PUBLISHED'))

            for doc in fallback_query.stream():
                if doc.id not in blog_ids:
                    data = doc.to_dict()
                    if data.get('embedding'):
                        data['id'] = doc.id
                        blogs.append(data)

            return blogs[:limit]
        except Exception as e:
            print(f"❌ Error fetching blogs with embeddings: {e}")
            return []

    def get_blogs_without_embeddings(self, user_id=None, limit=100):
        """
        Fetch published blogs that don't have embeddings yet.
        Used for backfilling embeddings.
        """
        try:
            blogs = []

            if user_id:
                # Query for specific user
                query = self.db.collection(self.collection_name)\
                    .where(filter=FieldFilter('site_owner_id', '==', user_id))\
                    .where(filter=FieldFilter('status', '==', 'PUBLISHED'))
            else:
                # Query all published blogs
                query = self.db.collection(self.collection_name)\
                    .where(filter=FieldFilter('status', '==', 'PUBLISHED'))

            for doc in query.stream():
                data = doc.to_dict()
                # Only include blogs without embeddings
                if not data.get('embedding'):
                    data['id'] = doc.id
                    blogs.append(data)

            return blogs[:limit]
        except Exception as e:
            print(f"❌ Error fetching blogs without embeddings: {e}")
            return []