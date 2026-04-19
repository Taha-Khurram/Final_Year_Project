# import google.generativeai as genai
from google import generativeai as genai
from flask import current_app
import json

class OutlineAgent:
    def __init__(self):
        # Always configure inside the class or factory to ensure app context
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def generate_outline(self, topic):
        prompt = f"Create a structured SEO blog outline for: {topic}. Return ONLY a JSON list of strings."
        response = self.model.generate_content(prompt)
        return [line.strip() for line in response.text.split('\n') if line.strip()] 