from app.agents.outline_agent import OutlineAgent
from app.agents.content_agent import ContentAgent
from app.agents.formatting_agent import FormattingAgent
from app.agents.seo_agent import SEOAgent
from app.agents.humanize_agent import HumanizeAgent
from app.utils.parallel import run_parallel_simple, TimedExecution


class BlogAgent:
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        self.formatting_agent = FormattingAgent()
        self.seo_agent = SEOAgent()
        self.humanize_agent = HumanizeAgent()

    def run_pipeline(self, user_prompt, enable_seo=False, enable_humanize=False, region="PK"):
        """
        Optimized AI blog generation pipeline.
        SEO is disabled by default during generation for speed.
        Use run_seo_analysis() separately for full SEO optimization.

        Args:
            user_prompt: Topic/prompt for the blog
            enable_seo: Whether to run full SEO optimization (slower, default False)
            region: Target region for SEO keywords (default Pakistan)
        """
        print(f"--- Starting Optimized AI Pipeline ---")

        try:
            # Step 1: Generate Outline (required first)
            with TimedExecution("Outline Generation"):
                outline = self.outline_agent.generate_outline(user_prompt)

            if not outline or not isinstance(outline, list):
                raise ValueError("Outline generation failed or returned empty data.")

            # Step 2: Generate Full Content (depends on outline)
            with TimedExecution("Content Generation"):
                content_data = self.content_agent.generate_full_blog(outline)

            if not content_data or 'markdown' not in content_data:
                raise KeyError("Content agent failed to return 'markdown' data.")

            markdown_text = content_data['markdown']
            final_title = user_prompt.title()

            # Step 2.5: Humanize Content (optional, before formatting)
            if enable_humanize:
                with TimedExecution("Humanization"):
                    try:
                        humanize_result = self.humanize_agent.humanize_content(
                            markdown=markdown_text, topic=user_prompt
                        )
                        if humanize_result.get('humanization_applied'):
                            markdown_text = humanize_result['markdown']
                            print("✅ Content humanized successfully")
                    except Exception as humanize_error:
                        print(f"⚠️ Humanization skipped: {humanize_error}")

            # Step 3: Format Content (run immediately, no SEO delay)
            with TimedExecution("Formatting"):
                formatted_data = self.formatting_agent.format_blog(
                    content=markdown_text,
                    title=final_title
                )

            # Step 4: Quick SEO analysis (optional, lightweight)
            seo_data = None
            if enable_seo:
                with TimedExecution("SEO Analysis"):
                    try:
                        # Use analyze_only for speed - no content rewriting
                        seo_data = self.seo_agent.analyze_only(
                            title=final_title,
                            content=markdown_text
                        )
                        seo_data['enabled'] = True
                    except Exception as seo_error:
                        print(f"SEO analysis skipped: {seo_error}")
                        seo_data = {"error": str(seo_error), "skipped": True}

            # Step 5: Package for Firestore
            word_count = formatted_data['statistics']['word_count']

            return {
                "title": final_title,
                "outline": outline,
                "content": {
                    "markdown": markdown_text,
                    "html": formatted_data['html'],
                    "original_markdown": content_data['markdown']
                },
                "formatting": {
                    "toc": formatted_data['toc'],
                    "toc_html": formatted_data['toc_html'],
                    "reading_time": formatted_data['reading_time_text'],
                    "reading_time_minutes": formatted_data['reading_time_minutes'],
                    "statistics": formatted_data['statistics'],
                    "has_code": formatted_data['has_code_blocks'],
                    "has_images": formatted_data['has_images'],
                    "has_tables": formatted_data['has_tables']
                },
                "seo": seo_data if seo_data else {"enabled": False},
                "metadata": {
                    "word_count": word_count,
                    "model_used": "gemini-3-flash-preview",
                    "status": "success",
                    "seo_enabled": enable_seo,
                    "humanized": enable_humanize,
                    "target_region": region if enable_seo else None
                }
            }

        except (IndexError, KeyError, ValueError) as e:
            print(f"Pipeline Error: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "partial_outline": outline if 'outline' in locals() else None
            }
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return {"error": "An unexpected system error occurred.", "status": "failed"}

    def run_seo_analysis(self, title, content, region="PK"):
        """
        Run SEO analysis only (without full blog generation)
        Useful for analyzing existing content
        """
        try:
            return self.seo_agent.optimize_blog(title, content, region)
        except Exception as e:
            print(f"SEO Analysis Error: {e}")
            return {"error": str(e), "status": "failed"}

    def format_content(self, content, title=""):
        """
        Format content only (without generation)
        Useful for formatting existing/imported content
        """
        try:
            return self.formatting_agent.format_blog(content, title)
        except Exception as e:
            print(f"Formatting Error: {e}")
            return {"error": str(e), "status": "failed"}