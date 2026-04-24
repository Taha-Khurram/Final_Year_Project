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

            # Check if it's a JSON string (starts with {) or a file path
            if isinstance(cert_path_or_json, str) and cert_path_or_json.strip().startswith('{'):
                # It's a JSON string - parse it
                cert_dict = json.loads(cert_path_or_json)
                cred = credentials.Certificate(cert_dict)
            elif isinstance(cert_path_or_json, str) and os.path.exists(cert_path_or_json):
                # It's a file path
                cred = credentials.Certificate(cert_path_or_json)
            else:
                # Try parsing as JSON anyway
                try:
                    cert_dict = json.loads(cert_path_or_json)
                    cred = credentials.Certificate(cert_dict)
                except:
                    raise ValueError(f"Invalid Firebase certificate: not a valid file path or JSON string")

            firebase_admin.initialize_app(cred)
            cls._instance = firestore.client()
            print("--- Firebase Admin SDK Initialized Successfully ---")

        return cls._instance