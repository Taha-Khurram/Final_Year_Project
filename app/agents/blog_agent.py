from app.agents.outline_agent import OutlineAgent
from app.agents.content_agent import ContentAgent
from app.agents.formatting_agent import FormattingAgent
from app.agents.seo_agent import SEOAgent


class BlogAgent:
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        self.formatting_agent = FormattingAgent()
        self.seo_agent = SEOAgent()

    def run_pipeline(self, user_prompt, enable_seo=True, region="PK"):
        """
        Full AI blog generation pipeline

        Args:
            user_prompt: Topic/prompt for the blog
            enable_seo: Whether to run SEO optimization (default True)
            region: Target region for SEO keywords (default Pakistan)
        """
        print(f"--- Starting Full AI Pipeline ---")

        try:
            # Step 1: Generate Outline
            print("Step 1: Generating Outline...")
            outline = self.outline_agent.generate_outline(user_prompt)

            if not outline or not isinstance(outline, list):
                raise ValueError("Outline generation failed or returned empty data.")

            # Step 2: Generate Full Content
            print("Step 2: Expanding into Full Blog...")
            content_data = self.content_agent.generate_full_blog(outline)

            if not content_data or 'markdown' not in content_data:
                raise KeyError("Content agent failed to return 'markdown' data.")

            markdown_text = content_data['markdown']

            # Step 3: Format Content
            print("Step 3: Formatting content...")
            formatted_data = self.formatting_agent.format_blog(
                content=markdown_text,
                title=user_prompt.title()
            )

            # Step 4: SEO Optimization (optional)
            seo_data = None
            if enable_seo:
                print("Step 4: Optimizing for SEO...")
                try:
                    seo_data = self.seo_agent.optimize_blog(
                        title=user_prompt.title(),
                        content=markdown_text,
                        region=region
                    )

                    # Use SEO-optimized content if available
                    if seo_data and seo_data.get('optimized'):
                        optimized = seo_data['optimized']
                        if optimized.get('optimized_content'):
                            markdown_text = optimized['optimized_content']
                            # Re-format with optimized content
                            formatted_data = self.formatting_agent.format_blog(
                                content=markdown_text,
                                title=optimized.get('optimized_title', user_prompt.title())
                            )
                except Exception as seo_error:
                    print(f"SEO optimization skipped: {seo_error}")
                    seo_data = {"error": str(seo_error), "skipped": True}

            # Step 5: Package for Firestore
            print("Step 5: Packaging data...")
            word_count = formatted_data['statistics']['word_count']

            return {
                "title": seo_data['optimized']['optimized_title'] if seo_data and seo_data.get('optimized') else user_prompt.title(),
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