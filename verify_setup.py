import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask

# Import system components
from config import Config
from app.firebase.firebase_admin import FirebaseLoader
from app.firebase.firestore_service import FirestoreService  # New Import
from app.agents.blog_agent import BlogAgent

def verify_all():
    load_dotenv()
    print("--- 🔍 STARTING PRODUCTION READINESS CHECK ---")

    # Initialize Flask context for config access
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # 1. TEST FIREBASE ADMIN SDK & FIRESTORE SERVICE
        print("\n[1/3] Initializing Firestore Service...")
        try:
            # This ensures the Firebase Admin SDK starts
            FirebaseLoader.get_instance(app.config['FIREBASE_SERVICE_ACCOUNT'])
            db_service = FirestoreService()
            print("✅ FIREBASE: Service initialized and connected.")
        except Exception as e:
            print(f"❌ FIREBASE ERROR: {e}")
            return

        # 2. TEST AGENT ORCHESTRATION (The Pipeline)
        print("\n[2/3] Running AI Pipeline (Outline + Content)...")
        generated_blog = None
        try:
            agent = BlogAgent()
            test_prompt = "The impact of generative AI in 2026"
            generated_blog = agent.run_pipeline(test_prompt)
            
            if generated_blog.get('content'):
                print("✅ AGENT: Pipeline successfully generated content.")
            else:
                print("❌ AGENT ERROR: Pipeline returned empty data.")
        except Exception as e:
            print(f"❌ PIPELINE ERROR: {e}")

        # 3. TEST LIVE DATABASE WRITE
        if generated_blog:
            print("\n[3/3] Sending generated data to Firestore...")
            try:
                # Add a test flag so you can find it easily in the console
                generated_blog["metadata"]["test_run"] = True
                
                # Use our service to save it
                doc_id = db_service.create_draft(generated_blog)
                
                print(f"✅ SUCCESS: Data saved to Firestore!")
                print(f"👉 DOCUMENT ID: {doc_id}")
                print(f"🔗 View it here: https://console.firebase.google.com/u/0/project/{os.getenv('FB_PROJECT_ID')}/firestore/data/~2Fblogs~2F{doc_id}")
            except Exception as e:
                print(f"❌ WRITE ERROR: {e}")

    print("\n--- ✅ VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_all()
    