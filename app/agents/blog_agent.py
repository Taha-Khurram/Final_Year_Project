from app.agents.outline_agent import OutlineAgent
from app.agents.content_agent import ContentAgent


class BlogAgent:
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()

    def run_pipeline(self, user_prompt):
        print(f"--- Starting Full AI Pipeline ---")
        
        try:
            # Step 1: Generate Outline
            print("Generating Outline...")
            outline = self.outline_agent.generate_outline(user_prompt)
            
            if not outline or not isinstance(outline, list):
                raise ValueError("Outline generation failed or returned empty data.")

            # Step 2: Generate Full Content
            print("Expanding into Full Blog...")
            content_data = self.content_agent.generate_full_blog(outline)
            
            if not content_data or 'markdown' not in content_data:
                raise KeyError("Content agent failed to return 'markdown' data.")
            

            # Step 4: Package for Firestore
            print("Packaging data...")
            markdown_text = content_data['markdown']
            word_count = len(markdown_text.split())
            
            return {
                "title": user_prompt.title(),
                "outline": outline,
                "content": content_data,
                "metadata": {
                    "word_count": word_count,
                    "model_used": "gemini-3-flash",
                    "status": "success"
                }
            }

        except (IndexError, KeyError, ValueError) as e:
            print(f"❌ Pipeline Error: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "partial_outline": outline if 'outline' in locals() else None
            }
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return {"error": "An unexpected system error occurred.", "status": "failed"}