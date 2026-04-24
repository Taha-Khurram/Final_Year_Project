import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

class FirebaseLoader:
    _instance = None

    @classmethod
    def get_instance(cls, cert_path_or_json=None):
        if cls._instance is None:
            if cert_path_or_json is None:
                raise ValueError("Firebase certificate path or JSON required for first-time initialization.")

            cred = None

            # Check if it's a file path that exists
            if isinstance(cert_path_or_json, str) and os.path.exists(cert_path_or_json):
                cred = credentials.Certificate(cert_path_or_json)
            else:
                # Try to parse as JSON
                try:
                    # Handle if it's already a dict
                    if isinstance(cert_path_or_json, dict):
                        cert_dict = cert_path_or_json
                    else:
                        # Clean up the string and parse
                        json_str = cert_path_or_json.strip()
                        cert_dict = json.loads(json_str)
                    cred = credentials.Certificate(cert_dict)
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error: {e}")
                    print(f"First 100 chars: {cert_path_or_json[:100] if cert_path_or_json else 'None'}")
                    raise ValueError(f"Invalid Firebase certificate JSON: {e}")
                except Exception as e:
                    print(f"Firebase Error: {e}")
                    raise ValueError(f"Invalid Firebase certificate: {e}")

            firebase_admin.initialize_app(cred)
            cls._instance = firestore.client()
            print("--- Firebase Admin SDK Initialized Successfully ---")

        return cls._instance