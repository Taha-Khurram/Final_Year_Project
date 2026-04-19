import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseLoader:
    _instance = None

    @classmethod
    def get_instance(cls, cert_path=None):
        if cls._instance is None:
            if cert_path is None:
                raise ValueError("Firebase certificate path required for first-time initialization.")
            
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
            cls._instance = firestore.client()
            print("--- Firebase Admin SDK Initialized Successfully ---")
        
        return cls._instance