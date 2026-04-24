import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

class FirebaseLoader:
    _instance = None

    @classmethod
    def get_instance(cls, cert_path_or_json=None):
        if cls._instance is None:
            # Try multiple sources for Firebase credentials
            firebase_creds = cert_path_or_json or os.getenv('FIREBASE_SERVICE_ACCOUNT')

            if not firebase_creds:
                print("ERROR: No Firebase credentials found!")
                print(f"FIREBASE_SERVICE_ACCOUNT env: {os.getenv('FIREBASE_SERVICE_ACCOUNT', 'NOT SET')[:50] if os.getenv('FIREBASE_SERVICE_ACCOUNT') else 'NOT SET'}")
                raise ValueError("Firebase credentials not found. Set FIREBASE_SERVICE_ACCOUNT environment variable.")

            cred = None

            # Check if it's a file path that exists
            if isinstance(firebase_creds, str) and os.path.exists(firebase_creds):
                print(f"Loading Firebase from file: {firebase_creds}")
                cred = credentials.Certificate(firebase_creds)
            else:
                # Try to parse as JSON
                try:
                    if isinstance(firebase_creds, dict):
                        cert_dict = firebase_creds
                    else:
                        json_str = firebase_creds.strip()
                        cert_dict = json.loads(json_str)
                    print(f"Loading Firebase from JSON (project: {cert_dict.get('project_id', 'unknown')})")
                    cred = credentials.Certificate(cert_dict)
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {e}")
                    print(f"Value type: {type(firebase_creds)}")
                    print(f"First 100 chars: {str(firebase_creds)[:100]}")
                    raise ValueError(f"Invalid Firebase JSON: {e}")
                except Exception as e:
                    print(f"Firebase Error: {e}")
                    raise ValueError(f"Invalid Firebase certificate: {e}")

            firebase_admin.initialize_app(cred)
            cls._instance = firestore.client()
            print("--- Firebase Admin SDK Initialized Successfully ---")

        return cls._instance