import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # Reconstruct the JS object for the frontend
    FIREBASE_CONFIG = {
        "apiKey": os.getenv("FB_API_KEY"),
        "authDomain": os.getenv("FB_AUTH_DOMAIN"),
        "projectId": os.getenv("FB_PROJECT_ID"),
        "storageBucket": os.getenv("FB_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FB_SENDER_ID"),
        "appId": os.getenv("FB_APP_ID"),
        "measurementId": os.getenv("FB_MEASUREMENT_ID")
    }
    
# For Firebase JS SDK v7.20.0 and later, measurementId is optional
firebaseConfig = {
  "apiKey": "AIzaSyDLj13Gxr9pZCT4drZxvf4vpWR7pD5LEtA",
  "authDomain": "scriptly-80803.firebaseapp.com",
  "projectId": "scriptly-80803",
  "storageBucket": "scriptly-80803.firebasestorage.app",
  "messagingSenderId": "1082423526791",
  "appId": "1:1082423526791:web:ea1ea304119e110a31bf22",
  "measurementId": "G-D4R1CPD5HF"
};