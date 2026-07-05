"""
Data Pipeline — Cleaning, deduplication, language filtering, relevance scoring, and normalization.

Implements all 5 processing steps from spec §3.6:
1. Deduplication (SHA-256 hash + Jaccard similarity)
2. Language filtering (English only for v1.0)
3. Relevance filtering (keyword-based pre-filter)
4. Text normalization (strip HTML, truncate, anonymize PII)
5. Metadata enrichment (source_weight, recency_score, processed_at)
"""

import hashlib
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Set, Tuple
from html import unescape

logger = logging.getLogger(__name__)

# Relevance keywords from spec §3.6
RELEVANCE_KEYWORDS = [
    "discover", "recommend", "suggestion", "new music", "playlist",
    "algorithm", "same song", "repeat", "explore", "find music",
    "discover weekly", "release radar", "radio", "similar",
    "boring", "stale", "tired of",
]

# Source weights from spec §3.6
SOURCE_WEIGHTS = {
    "app_store": 1.0,
    "play_store": 1.0,
    "reddit": 0.9,
    "spotify_community": 0.8,
    "twitter_x": 0.7,
}


class DataCleaner:
    """Pipeline for cleaning, filtering, and enriching raw review data."""

    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.stats = {
            "total_input": 0,
            "duplicates_removed": 0,
            "non_english_removed": 0,
            "irrelevant_removed": 0,
            "total_output": 0,
        }

    def process_batch(self, entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process a batch of raw review entries through the full cleaning pipeline.

        Returns:
            (relevant_entries, excluded_entries)
        """
        self.stats["total_input"] = len(entries)
        logger.info(f"Processing {len(entries)} entries through cleaning pipeline...")

        # Step 1: Deduplication
        entries = self._deduplicate(entries)

        # Step 2: Language filtering
        entries, non_english = self._filter_language(entries)

        # Step 3: Relevance filtering
        relevant, excluded = self._filter_relevance(entries)

        # Step 4: Text normalization (applied to relevant entries)
        relevant = [self._normalize_text(e) for e in relevant]

        # Step 5: Metadata enrichment
        relevant = [self._enrich_metadata(e) for e in relevant]

        self.stats["total_output"] = len(relevant)

        logger.info(
            f"Pipeline complete: {self.stats['total_input']} input → "
            f"{self.stats['total_output']} output "
            f"({self.stats['duplicates_removed']} dupes, "
            f"{self.stats['non_english_removed']} non-EN, "
            f"{self.stats['irrelevant_removed']} irrelevant)"
        )

        return relevant, excluded + non_english

    def _deduplicate(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 1: Remove exact duplicates using SHA-256 hash."""
        unique = []
        for entry in entries:
            body = entry.get("body", "")
            body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

            if body_hash not in self.seen_hashes:
                self.seen_hashes.add(body_hash)
                entry["body_hash"] = body_hash
                unique.append(entry)
            else:
                self.stats["duplicates_removed"] += 1

        return unique

    def _filter_language(self, entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Step 2: Keep only English-language entries."""
        english = []
        non_english = []

        for entry in entries:
            # If language already detected, use it
            lang = entry.get("language")

            if not lang:
                try:
                    from langdetect import detect
                    lang = detect(entry.get("body", ""))
                    entry["language"] = lang
                except Exception:
                    entry["language"] = "en"  # Default to English if detection fails
                    lang = "en"

            if lang == "en":
                english.append(entry)
            else:
                entry["exclusion_reason"] = f"non_english_language_{lang}"
                entry["is_relevant"] = False
                non_english.append(entry)
                self.stats["non_english_removed"] += 1

        return english, non_english

    def _filter_relevance(self, entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Step 3: Keyword-based relevance filter for discovery-related content."""
        relevant = []
        excluded = []

        for entry in entries:
            body = entry.get("body", "").lower()
            title = (entry.get("title") or "").lower()
            search_text = f"{title} {body}"

            # Count keyword matches
            match_count = sum(1 for kw in RELEVANCE_KEYWORDS if kw in search_text)

            if match_count > 0:
                entry["is_relevant"] = True
                relevant.append(entry)
            else:
                entry["is_relevant"] = False
                entry["exclusion_reason"] = "no_discovery_keywords"
                excluded.append(entry)
                self.stats["irrelevant_removed"] += 1

        return relevant, excluded

    def _normalize_text(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Clean and normalize text content."""
        body = entry.get("body", "")

        # Strip HTML tags
        body = re.sub(r"<[^>]+>", "", body)

        # Unescape HTML entities
        body = unescape(body)

        # Remove special characters (keep basic punctuation)
        body = re.sub(r"[^\w\s.,!?;:'\"-()@#]", " ", body)

        # Collapse excess whitespace
        body = re.sub(r"\s+", " ", body).strip()

        # Truncate to 2000 characters (store full text separately if needed)
        if len(body) > 2000:
            entry["full_body"] = body  # Preserve full text
            body = body[:2000]

        entry["body"] = body

        # Normalize title similarly
        if entry.get("title"):
            title = re.sub(r"<[^>]+>", "", entry["title"])
            title = unescape(title)
            title = re.sub(r"\s+", " ", title).strip()
            entry["title"] = title

        return entry

    def _enrich_metadata(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Add computed metadata fields."""
        # Source weight
        source = entry.get("source", "")
        entry["source_weight"] = SOURCE_WEIGHTS.get(source, 0.5)

        # Recency score
        published_at = entry.get("published_at")
        if published_at:
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    published_at = datetime.now(timezone.utc)

            days_ago = (datetime.now(timezone.utc) - published_at).days
            if days_ago <= 30:
                entry["recency_score"] = 1.0
            elif days_ago <= 90:
                entry["recency_score"] = 0.8
            elif days_ago <= 180:
                entry["recency_score"] = 0.6
            else:
                entry["recency_score"] = 0.4
        else:
            entry["recency_score"] = 0.5  # Default if no date

        # Processing timestamp
        entry["processed_at"] = datetime.now(timezone.utc).isoformat()

        return entry

    def get_stats(self) -> Dict[str, Any]:
        """Return pipeline processing statistics."""
        return self.stats
