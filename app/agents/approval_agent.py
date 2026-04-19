from app.firebase.firestore_service import FirestoreService

class ApprovalAgent:
    def __init__(self):
        self.db_service = FirestoreService()

    def create_initial_review(self, blog_data, user_id):
        """
        Mimics DraftsAgent but forces status to UNDER_REVIEW.
        Used for the 'Auto-Submit' pipeline.
        """
        # 1. Map fields correctly
        blog_data["author_id"] = user_id
        
        # 2. Fix the "Untitled" issue
        if "title" not in blog_data or not blog_data["title"]:
            blog_data["title"] = "New AI Blog (Pending Review)"

        # 3. Fix the content mapping (Standardize body format)
        if "content" not in blog_data:
            blog_data["content"] = {"body": "No content generated."}
        elif isinstance(blog_data["content"], dict) and "markdown" in blog_data["content"]:
            blog_data["content"]["body"] = blog_data["content"].pop("markdown")

        # 4. Set status to UNDER_REVIEW and initialize admin flags
        blog_data["status"] = "UNDER_REVIEW"
        blog_data["admin"] = {
            "review_required": True,
            "review_notes": "Generated and auto-submitted for review.",
            "approved_at": None
        }

        # 5. Save directly to Firestore
        blog_id = self.db_service.create_draft(blog_data)
        return blog_id

    def submit_for_review(self, blog_id):
        """Moves an existing DRAFT to UNDER_REVIEW."""
        update_data = {
            "status": "UNDER_REVIEW",
            "admin.review_required": True,
            "admin.review_notes": "Awaiting initial review."
        }
        success = self.db_service.update_blog(blog_id, update_data)
        
        if success:
            return {"status": "success", "message": "Submitted to Admin Approval"}
        else:
            return {"status": "error", "message": "Update failed"}

    def process_admin_action(self, blog_id, action, notes=None):
        """Action: 'APPROVE' or 'REJECT'"""
        status_map = {
            "APPROVE": "PUBLISHED",
            "REJECT": "REJECTED"
        }
        
        new_status = status_map.get(action.upper(), "UNDER_REVIEW")
        
        update_data = {
            "status": new_status,
            "admin.review_notes": notes,
            "admin.review_required": False
        }
        
        return self.db_service.update_blog(blog_id, update_data)