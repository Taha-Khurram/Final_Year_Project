import os
import resend
from flask import render_template_string

class EmailService:
    """
    Email service using Resend API.
    Free tier: 3,000 emails/month, no credit card required.
    Sign up at https://resend.com
    """

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
        self.from_name = os.getenv("FROM_NAME", "Newsletter")

        if self.api_key:
            resend.api_key = self.api_key

    def _get_from_address(self):
        """Format the from address with name."""
        return f"{self.from_name} <{self.from_email}>"

    def send_single(self, to_email: str, subject: str, html_content: str):
        """Send email to a single recipient."""
        if not self.api_key:
            return {"success": False, "error": "RESEND_API_KEY not configured"}

        try:
            params = {
                "from": self._get_from_address(),
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            response = resend.Emails.send(params)
            return {"success": True, "id": response.get("id")}
        except Exception as e:
            print(f"Email send error: {e}")
            return {"success": False, "error": str(e)}

    def send_newsletter(self, to_emails: list, subject: str, html_content: str):
        """
        Send newsletter to multiple recipients.
        Uses individual sends for better deliverability and tracking.
        """
        if not self.api_key:
            return {"success": False, "error": "RESEND_API_KEY not configured"}

        if not to_emails:
            return {"success": False, "error": "No recipients provided"}

        results = {
            "success": True,
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for email in to_emails:
            try:
                params = {
                    "from": self._get_from_address(),
                    "to": [email],
                    "subject": subject,
                    "html": html_content
                }
                resend.Emails.send(params)
                results["sent"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"email": email, "error": str(e)})

        if results["failed"] > 0 and results["sent"] == 0:
            results["success"] = False

        return results

    def send_batch(self, subscribers: list, subject: str, html_content: str,
                   base_url: str = "", site_name: str = "Newsletter"):
        """
        Send newsletter to all subscribers in batches.
        Personalizes unsubscribe link for each subscriber.

        Args:
            subscribers: List of subscriber dicts with 'email' key
            subject: Email subject line
            html_content: HTML content (can include {{ email }} for personalization)
            base_url: Base URL for unsubscribe links
            site_name: Name to show in footer
        """
        if not self.api_key:
            return {"success": False, "error": "RESEND_API_KEY not configured"}

        if not subscribers:
            return {"success": False, "error": "No subscribers"}

        results = {
            "success": True,
            "total": len(subscribers),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for subscriber in subscribers:
            email = subscriber.get('email')
            if not email:
                continue

            try:
                # Personalize content with subscriber email for unsubscribe
                personalized_html = html_content.replace(
                    "{{ email }}", email
                ).replace(
                    "{{ unsubscribe_url }}",
                    f"{base_url}/unsubscribe?email={email}"
                )

                params = {
                    "from": self._get_from_address(),
                    "to": [email],
                    "subject": subject,
                    "html": personalized_html
                }
                resend.Emails.send(params)
                results["sent"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"email": email, "error": str(e)})

        if results["sent"] == 0:
            results["success"] = False

        return results

    def test_connection(self):
        """Test if API key is valid by checking Resend API."""
        if not self.api_key:
            return {"valid": False, "error": "RESEND_API_KEY not set"}

        try:
            # Try to list domains (lightweight API call)
            resend.Domains.list()
            return {"valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}
