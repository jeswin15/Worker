import time
import json
import logging
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.config import Config

class LLMEvaluator:
    def __init__(self):
        self.logger = logging.getLogger("engine.llm")
        self.logger.setLevel(logging.INFO)

        # Modern LangChain parameters for better OpenRouter compatibility
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,
            default_headers={
                "HTTP-Referer": "https://holocene.vc",
                "X-Title": "Holocene Startup Sourcing Agent",
            }
        )
        
        # Verify key loading (First 10 chars only)
        key_preview = f"{Config.OPENROUTER_API_KEY[:10]}..." if Config.OPENROUTER_API_KEY else "Missing"
        self.logger.info(f"LLM Evaluator initialized with model: {Config.LLM_MODEL} and key: {key_preview}")

        self.prompt = self._create_prompt()

    def _create_prompt(self):
        template = """You are a VC Investment Analyst at Holocene.
Evaluate this startup against the Holocene Investment Thesis and respond ONLY with valid JSON (no markdown, no explanation).

HOLOCENE THESIS:
- Sectors: Blockchain, Biotech, Health, Commerce, Tech, Space
- Geography: Europe or North America
- Stage: Pre-seed to Series A
- Raising: $1M-$10M
- SDG alignment required
- Must improve human wellbeing
- Innovation required

SCORING (0-20 each, total 100):
1. sector: How well it fits target sectors
2. geography: Is it in Europe or North America?
3. funding: Is the stage/amount within bounds?
4. sdg: Does it align with SDGs?
5. innovation: How innovative is it?

INPUT:
Source: {source}
Title: {title}
Link: {link}
Content: {content}

Respond with this exact JSON structure:
{{"company_name": "...", "description": "...", "website": "...", "industry": "...", "stage": "...", "funding_info": "...", "sdg_alignment": "...", "innovation_level": "High|Medium|Low", "score_breakdown": {{"sector": 0, "geography": 0, "funding": 0, "sdg": 0, "innovation": 0}}, "rationale": "...", "recommendation": "Progress|Save|Ignore"}}"""
        return ChatPromptTemplate.from_template(template)

    def evaluate(self, item: dict) -> dict:
        """Evaluates a single startup item using the LLM with rate-limit retry."""
        self.logger.info(f"Evaluating startup: {item.get('title')}")

        formatted_prompt = self.prompt.format_messages(
            source=item.get("source", "Unknown"),
            title=item.get("title", ""),
            link=item.get("link", ""),
            content=item.get("summary", "")[:500],  # Truncate to save tokens
        )

        # Retry loop for rate limits
        for attempt in range(5):
            try:
                response = self.llm.invoke(formatted_prompt)
                evaluation = self._parse_response(response.content)
                if evaluation:
                    scores = evaluation.get("score_breakdown", {})
                    if isinstance(scores, str):
                        try:
                            scores = json.loads(scores)
                        except json.JSONDecodeError:
                            scores = {}
                    total = sum(int(scores.get(k, 0)) for k in ["sector", "geography", "funding", "sdg", "innovation"])
                    evaluation["confidence_score"] = total
                    evaluation["score_breakdown"] = scores
                    return evaluation
                return None
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate limit" in err_str.lower():
                    wait_time = 10 * (attempt + 1)
                    self.logger.warning(f"Rate limited. Waiting {wait_time}s before retry ({attempt+1}/5)...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Error evaluating {item.get('title')}: {e}")
                    return None

        self.logger.error(f"Failed after 5 retries for {item.get('title')}")
        return None

    def _parse_response(self, content: str) -> dict:
        """Try to extract JSON from the LLM response."""
        # Remove markdown code-block fences if present
        content = content.strip()
        content = re.sub(r"^```(?:json)?", "", content)
        content = re.sub(r"```$", "", content)
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object within the text
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            self.logger.error(f"Could not parse LLM response as JSON: {content[:200]}")
            return None
