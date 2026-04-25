import re
import random
from google import generativeai as genai
from flask import current_app


class HumanizeAgent:
    """
    Single-call content humanization agent with post-processing.
    Rewrites AI-generated content to bypass AI detection tools
    while preserving meaning, structure, and SEO value.
    Uses ONE API call + deterministic post-processing.
    """

    def __init__(self):
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        self.generation_config = genai.types.GenerationConfig(
            temperature=1.2,
            top_p=0.92,
            max_output_tokens=16384,
        )

    def humanize_content(self, markdown, topic=""):
        """
        Main entry point: humanize AI-generated markdown content.
        LLM rewrite + deterministic post-processing for maximum human score.

        Args:
            markdown: Raw AI-generated markdown text
            topic: Blog topic for context-aware voice injection

        Returns:
            dict with 'markdown', 'original_markdown', 'humanization_applied'
        """
        original_markdown = markdown

        try:
            # Step 1: LLM rewrite (single API call)
            humanized = self._humanize_full(markdown, topic)

            # Step 2: Deterministic post-processing (no API call)
            humanized = self._post_process(humanized)

            # Step 3: Validate structure preserved
            humanized = self._validate(original_markdown, humanized)

            return {
                "markdown": humanized,
                "original_markdown": original_markdown,
                "humanization_applied": True
            }

        except Exception as e:
            print(f"❌ HumanizeAgent Error: {e}")
            return {
                "markdown": original_markdown,
                "original_markdown": original_markdown,
                "humanization_applied": False
            }

    def _humanize_full(self, markdown, topic):
        """Rewrite the entire blog in a single API call with persona-driven humanization."""
        prompt = f"""You are Marcus, a 34-year-old freelance writer and blogger who's been covering {topic} for about 6 years. You have a casual-but-knowledgeable writing style — you explain complex things simply, throw in personal takes, and aren't afraid to be a bit blunt. You write the way you'd talk to a smart friend over coffee. You sometimes ramble slightly, catch yourself, and get back on track.

Your task: Completely REWRITE the blog content below in YOUR voice. Not edit it. Not polish it. REWRITE it from scratch using the same facts, structure, and headings.

═══ WHY THIS MATTERS ═══
AI detectors (GPTZero, Originality.ai, ZeroGPT) flag content based on:
- Uniform perplexity (every sentence equally "smooth") → You must make some sentences messy, some clean
- Low burstiness (all sentences similar length) → You must wildly vary sentence lengths
- Predictable word choices (the "AI voice") → You must use surprising, specific vocabulary
- Perfect grammar throughout → You must include natural imperfections
- Absence of personal perspective → You must inject YOUR takes

═══ WHAT AI TEXT LOOKS LIKE (AVOID ALL OF THIS) ═══
BAD: "In today's rapidly evolving digital landscape, it is crucial to leverage cutting-edge technologies to streamline your workflow and optimize productivity."
GOOD: "Look, I've been doing this long enough to know — most productivity advice is garbage. But there are maybe 3-4 tools that actually changed how I work. Let me break those down."

BAD: "Furthermore, implementing a comprehensive strategy can facilitate better outcomes and foster meaningful growth."
GOOD: "And here's what nobody tells you about strategy: half of it is just showing up consistently. I spent way too long overcomplicating this before I figured that out."

═══ STRUCTURAL RULES ═══
1. SENTENCE LENGTH — wildly vary it. Some sentences: 3-5 words. Others: 30-40 word run-ons connected with dashes and commas. Never 3+ sentences of similar length in a row.
2. PARAGRAPH LENGTH — some paragraphs are just one punchy sentence. Others are 5-6 sentences where you really dig in. Mix it up unpredictably.
3. KILL THESE TRANSITIONS — never use: "Furthermore", "Moreover", "Additionally", "In conclusion", "It is important to note", "Firstly/Secondly", "In today's world". Instead use: "Here's the thing —", "Okay so", "That said,", "Look,", "The flip side?", "Now this is where it gets interesting", "Real talk:", "So yeah,".
4. SENTENCE OPENERS — every sentence in a paragraph MUST start differently. Mix: questions, "And" starters, "But" starters, fragments, imperatives, numbers, names of tools/people.

═══ VOCABULARY RULES ═══
1. BANNED AI WORDS — replace every single one:
   "utilize/leverage/streamline/robust/cutting-edge/delve/crucial/facilitate/comprehensive/implement/optimize/paradigm/foster/harness/empower/seamless/plethora/myriad/encompass/pivotal/navigate(figurative)/landscape(figurative)/realm" → use plain English: "use, tap into, simplify, solid, latest, dig into, key, help, thorough, set up, improve, approach, build, grab, help, smooth, plenty of, many, cover, important, deal with, space, area"
2. CONTRACTIONS ALWAYS: "do not"→"don't", "it is"→"it's", "cannot"→"can't", "will not"→"won't", "they are"→"they're", "would not"→"wouldn't", "should not"→"shouldn't"
3. COLLOQUIAL SPRINKLES (3-5 per section): "honestly", "let's be real", "no-brainer", "here's the deal", "at the end of the day", "not gonna lie", "the thing is", "spoiler alert"
4. HEDGING LANGUAGE — humans express uncertainty. Use: "I think", "probably", "might be", "not 100% sure but", "from what I can tell", "seems like", "I'd guess". Don't make every statement sound certain.

═══ VOICE & PERSONALITY ═══
1. RHETORICAL QUESTIONS (2-3 per section): "But does this actually hold up?", "Sound familiar?", "So what's the catch?", "Why does this matter?", "Ever noticed how...?"
2. SELF-CORRECTIONS: Include 1-2 moments where you rephrase: "Well, actually...", "Okay let me rephrase that —", "Actually scratch that,", "Wait, that's not quite right —"
3. PERSONAL TAKES (1-2 per section): "In my experience,", "I'd argue", "Hot take:", "Unpopular opinion:", "What I've found works best is"
4. MINI-ANECDOTES: "I ran into this exact problem last year when...", "A client once asked me...", "I remember reading somewhere that...", "I've seen this go wrong when..."
5. EMOTIONAL MICRO-REACTIONS: "This blew my mind", "Frustrating, right?", "That's the part that gets me", "Love this", "This drives me nuts"
6. FILLER DISCOURSE MARKERS: Occasionally use "So yeah,", "Anyway,", "Right?", "I mean,", "Point being," — the way people actually write blog posts
7. READER ADDRESS — switch between "you", "we", "I" naturally. Don't always address the reader the same way.
8. IMPERFECT GRAMMAR (strategic): 2-3 sentence fragments per section. Start some sentences with "And" or "But". Use em dashes (—) liberally. One or two run-on sentences per section.
9. E-E-A-T SIGNALS: "from what I've tested", "after spending way too much time on this", "based on actual results I've seen", "from hands-on experience", "I've been doing this for years and"
10. SPECIFIC OVER VAGUE: Replace "many tools" with "about 7 tools". Replace "significant improvement" with "roughly 40% better". Invent plausible specific numbers.

═══ HARD RULES ═══
- Keep ALL headings (##, ###) — same number, same hierarchy, wording can change slightly
- Keep ALL markdown formatting (bold, italic, lists, code blocks, links)
- Keep the same factual information — don't invent new claims, just reframe existing ones
- Content length should stay within ±25% of the original
- Return ONLY the rewritten markdown. No commentary. No code fences. No preamble like "Here's the rewritten version".

CONTENT TO REWRITE:
{markdown}"""

        response = self.model.generate_content(
            prompt, generation_config=self.generation_config
        )
        return self._clean_response(response.text)

    def _post_process(self, text):
        """
        Deterministic post-processing to disrupt AI detection patterns.
        These are text-level transformations no LLM would produce,
        which breaks the statistical fingerprint detectors look for.
        """
        lines = text.split('\n')
        processed = []

        for line in lines:
            # Skip headings, code blocks, and list items
            if re.match(r'^#{1,6}\s', line) or line.startswith('```') or re.match(r'^\s*[-*]\s', line):
                processed.append(line)
                continue

            # 1. Introduce contraction inconsistency (humans aren't consistent)
            #    Randomly expand ~10% of contractions back to full form
            if random.random() < 0.10:
                expansions = [
                    (r"\bdon't\b", "do not"),
                    (r"\bcan't\b", "cannot"),
                    (r"\bwon't\b", "will not"),
                    (r"\bit's\b", "it is"),
                    (r"\bthey're\b", "they are"),
                    (r"\bwe're\b", "we are"),
                    (r"\bdoesn't\b", "does not"),
                    (r"\bwouldn't\b", "would not"),
                ]
                pick = random.choice(expansions)
                line = re.sub(pick[0], pick[1], line, count=1)

            # 2. Swap some straight quotes with curly quotes (~15% of lines)
            if random.random() < 0.15 and '"' in line:
                # Replace first pair of straight quotes with curly
                line = re.sub(r'"([^"]+)"', '\u201c\\1\u201d', line, count=1)

            # 3. Swap double hyphens for em dashes or vice versa (~8%)
            if random.random() < 0.08:
                if ' -- ' in line:
                    line = line.replace(' -- ', ' \u2014 ', 1)
                elif ' \u2014 ' in line and line.count(' \u2014 ') > 1:
                    line = line.replace(' \u2014 ', ' -- ', 1)

            # 4. Occasionally add a trailing thought with ellipsis (~3% of non-empty body lines)
            if (random.random() < 0.03
                    and len(line) > 40
                    and line.endswith('.')
                    and not line.endswith('...')):
                trailing = random.choice([
                    "...but more on that later",
                    "...at least in my experience",
                    "...or so I've found",
                    "...which is interesting to think about",
                ])
                line = line[:-1] + trailing + "."

            processed.append(line)

        return '\n'.join(processed)

    def _clean_response(self, text):
        """Strip markdown code fences that LLMs sometimes wrap around output."""
        text = text.strip()
        # Remove ```markdown ... ``` or ``` ... ``` wrappers
        text = re.sub(r'^```(?:markdown)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        # Remove preamble like "Here's the rewritten version:" before first heading
        if re.search(r'^#', text, re.MULTILINE):
            stripped = re.sub(r'^.*?(?=^#)', '', text, count=1, flags=re.DOTALL | re.MULTILINE)
            if stripped.strip():
                text = stripped
        return text.strip()

    def _validate(self, original, humanized):
        """Validate humanized output preserves structure and reasonable length."""
        if not humanized or not humanized.strip():
            print("⚠️ Humanization returned empty — using original")
            return original

        orig_headings = re.findall(r'^#{1,3}\s+.+', original, re.MULTILINE)
        new_headings = re.findall(r'^#{1,3}\s+.+', humanized, re.MULTILINE)

        if len(orig_headings) > 0 and len(new_headings) == 0:
            print("⚠️ Humanization lost all headings — using original")
            return original

        orig_words = len(original.split())
        new_words = len(humanized.split())

        if orig_words > 0:
            ratio = new_words / orig_words
            if ratio < 0.70 or ratio > 1.30:
                print(f"⚠️ Word count changed too much ({orig_words} → {new_words}) — using original")
                return original

        return humanized
