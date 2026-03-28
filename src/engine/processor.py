from typing import List, Dict
import logging
import time
from src.ingestion.rss_collectors import get_rss_collectors
from src.ingestion.reddit_collector import RedditRSSCollector
from src.ingestion.hn_collector import HNCollector
from src.database.factory import get_db
from src.database.deduplicator import Deduplicator
from src.engine.llm_evaluator import LLMEvaluator
from src.engine.scoring import ScoringEngine
from src.utils.config import Config


class ProcessOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger("engine.orchestrator")
        self.logger.setLevel(logging.INFO)

        self.collectors = []
        self._initialize_collectors()

        self.db = get_db()
        self.deduplicator = Deduplicator()
        self.evaluator = LLMEvaluator()
        self.scoring = ScoringEngine()

    def _initialize_collectors(self):
        # Zero-Config / Public Sources (no API keys needed)
        self.collectors.extend(get_rss_collectors())
        self.collectors.append(RedditRSSCollector())
        self.collectors.append(HNCollector())

        # Key-Required Sources (only if configured)
        if Config.GITHUB_TOKEN:
            from src.ingestion.github_collector import GitHubCollector
            self.collectors.append(GitHubCollector())
        if Config.PRODUCT_HUNT_API_KEY:
            from src.ingestion.product_hunt_collector import ProductHuntCollector
            self.collectors.append(ProductHuntCollector())

    def run_cycle(self, days: int = 7):
        """Runs one full cycle of fetching, processing, and evaluation."""
        self.logger.info("=" * 60)
        self.logger.info("Starting new data collection cycle")
        self.logger.info("=" * 60)

        # 1. Fetch from all sources
        all_raw_items = []
        for collector in self.collectors:
            try:
                items = collector.fetch_recent(days=days)
                normalized = collector.normalize(items)
                all_raw_items.extend(normalized)
                self.logger.info(f"  {collector.source_name}: {len(items)} items")
            except Exception as e:
                self.logger.error(f"  {collector.source_name}: FAILED - {e}")

        self.logger.info(f"Total raw items fetched: {len(all_raw_items)}")

        # 2. Deduplicate against existing data
        existing_startups = self.db.get_all_startups()
        unique_items = []
        for item in all_raw_items:
            if not self.deduplicator.is_duplicate(item, existing_startups + unique_items):
                unique_items.append(item)

        self.logger.info(f"Unique new items to evaluate: {len(unique_items)}")

        # 3. Evaluate each item with LLM (respect rate limits)
        evaluated_count = 0
        saved_count = 0
        for i, item in enumerate(unique_items):
            self.logger.info(f"[{i+1}/{len(unique_items)}] Evaluating: {item.get('title', 'Unknown')[:60]}")

            evaluation = self.evaluator.evaluate(item)

            if evaluation:
                # Merge original data with LLM evaluation
                final_startup = {**item, **evaluation}
                score = final_startup.get("confidence_score", 0)

                if score >= 40:  # Lowered for demo to show more results
                    self.db.insert_startup(final_startup)
                    saved_count += 1
                    self.logger.info(f"  [SAVED] (score={score}): {final_startup.get('company_name', 'Unknown')}")
                else:
                    self.logger.info(f"  [SKIP] Low score ({score}), skipped")

                evaluated_count += 1
            else:
                self.logger.warning(f"  [FAIL] Evaluation failed, skipped")

            # Rate limit: wait between requests (free tier = 8 req/min)
            if i < len(unique_items) - 1:
                time.sleep(20)  # Increased delay for free-tier stability

        self.logger.info("=" * 60)
        self.logger.info(f"Cycle complete. Evaluated: {evaluated_count}, Saved: {saved_count}")
        self.logger.info("=" * 60)
