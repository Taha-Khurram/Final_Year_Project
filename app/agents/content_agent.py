import google.generativeai as genai
from flask import current_app

class ContentAgent:
    def __init__(self):
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        # Using the stable 2026 identifier for speed and quality
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def generate_full_blog(self, outline):
        """
        Expands an outline into a complete blog post.
        """
        prompt = (
            f"You are an expert copywriter. Expand the following outline into a "
            f"comprehensive, engaging blog post (approx 1200 words). "
            f"Use Markdown for structure, including bold text for emphasis and "
            f"bullet points for readability. \n\nOUTLINE:\n{outline}"
        )
        
        response = self.model.generate_content(prompt)
        
        return {
    "markdown": response.text,
    "html": "<article>{}</article>".format(
        response.text.replace("\n", "<br>")
    )
}
