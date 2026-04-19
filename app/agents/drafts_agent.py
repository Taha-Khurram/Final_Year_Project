from app.firebase.firestore_service import FirestoreService

class DraftsAgent:
    def __init__(self):
        self.db_service = FirestoreService()

    def create_initial_draft(self, blog_data, user_id):
        """Prepares generated data and saves it via FirestoreService."""
        
        # 1. Map fields correctly
        blog_data["author_id"] = user_id
        
        # 2. Fix the "Untitled" issue
        if "title" not in blog_data or not blog_data["title"]:
            blog_data["title"] = "New AI Blog"

        # 3. Fix the content mapping
        # Ensure the body is a string within the content object
        if "content" not in blog_data:
            blog_data["content"] = {"body": "No content generated."}
        elif isinstance(blog_data["content"], dict) and "markdown" in blog_data["content"]:
            # Standardize 'markdown' key from AI to 'body' key for Firestore
            blog_data["content"]["body"] = blog_data["content"].pop("markdown")
        elif isinstance(blog_data["content"], str):
            # If AI returned a raw string, wrap it in a dict
            content_str = blog_data["content"]
            blog_data["content"] = {"body": content_str}

        # 4. Set status
        # We use a string because FirestoreService.update_blog_status calls .upper()
        # This ensures the blog appears in the 'Drafts' section
        if "status" not in blog_data:
            blog_data["status"] = "DRAFT"

        # 5. Save - FIX: Pass both blog_data AND user_id
        blog_id = self.db_service.create_draft(blog_data, user_id)
        
        return blog_id

    def update_draft_content(self, blog_id, new_content):   
        """Updates the body of an existing draft."""
        update_data = {
            "content.body": new_content,
            "status": "DRAFT",
            "updated_at": datetime.utcnow()
        }
        # Assuming you have a general update_blog method in FirestoreService
        return self.db_service.db.collection("blogs").document(blog_id).update(update_data)