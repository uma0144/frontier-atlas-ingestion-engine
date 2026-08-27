"""
Deterministic Entity Resolution Engine:
Performs canonicalization, rule-based legal suffix stripping, alias matching,
and fuzzy matching against the seed canonical database. Tracks resolution audit logs.
"""

import re
import unicodedata
import logging
from typing import Tuple, List, Dict, Optional
from datetime import datetime, timezone
from rapidfuzz import fuzz
from src.resolver.seed_db import CANONICAL_SEED_COMPANIES
from src.schemas import EntityMappingRecord

logger = logging.getLogger("EntityResolver")


class EntityResolver:
    def __init__(self, fuzzy_threshold: float = 85.0):
        self.fuzzy_threshold = fuzzy_threshold
        self.mapping_logs: List[EntityMappingRecord] = []
        self._alias_map: Dict[str, str] = {}
        self._canonical_list: List[str] = list(CANONICAL_SEED_COMPANIES.keys())
        self._build_index()

    def _normalize_string(self, text: str) -> str:
        """Strip accents, lowercase, remove legal suffixes, and clean whitespace."""
        if not text:
            return ""
        # Unicode normalization (NFKD)
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
        text = text.strip()

        # Remove legal corporate suffixes
        legal_pattern = r'\b(inc\.?|incorporated|llc\.?|corp\.?|corporation|ltd\.?|limited|pbc|gmbh|co\.?|technologies|labs|sas|bv|ai|a\.i\.)\b'
        cleaned = re.sub(legal_pattern, '', text, flags=re.IGNORECASE)

        # Remove punctuation except alphanumeric and spaces
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        # Collapse multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def _build_index(self):
        """Build normalized reverse lookup index from canonical seed database."""
        for canonical, aliases in CANONICAL_SEED_COMPANIES.items():
            norm_canonical = self._normalize_string(canonical).lower()
            self._alias_map[norm_canonical] = canonical
            self._alias_map[canonical.lower()] = canonical

            for alias in aliases:
                norm_alias = self._normalize_string(alias).lower()
                self._alias_map[norm_alias] = canonical
                self._alias_map[alias.lower()] = canonical

    def resolve(self, raw_name: str, entity_type: str = "STARTUP") -> Tuple[str, float, str]:
        """
        Resolve a raw entity string to its canonical representation.
        Returns: (canonical_name, confidence, method)
        """
        if not raw_name or not raw_name.strip():
            return "Unknown Entity", 0.0, "FALLBACK"

        raw_clean = raw_name.strip()
        norm = self._normalize_string(raw_clean)
        norm_lower = norm.lower()

        # 1. Exact or Direct Alias Match in Seed Database
        if raw_clean.lower() in self._alias_map:
            canonical = self._alias_map[raw_clean.lower()]
            self._log_mapping(raw_clean, canonical, entity_type, 1.0, "EXACT_SEED_MATCH")
            return canonical, 1.0, "EXACT_SEED_MATCH"

        if norm_lower in self._alias_map:
            canonical = self._alias_map[norm_lower]
            self._log_mapping(raw_clean, canonical, entity_type, 0.98, "NORMALIZED_SEED_MATCH")
            return canonical, 0.98, "NORMALIZED_SEED_MATCH"

        # 2. Fuzzy Matching against Canonical Seed Names
        best_match = None
        best_score = 0.0

        for canonical_name in self._canonical_list:
            norm_seed = self._normalize_string(canonical_name).lower()
            score_token = fuzz.token_sort_ratio(norm_lower, norm_seed)
            score_ratio = fuzz.ratio(norm_lower, norm_seed)
            score = max(score_token, score_ratio)

            if score > best_score:
                best_score = score
                best_match = canonical_name

        if best_score >= self.fuzzy_threshold and best_match:
            confidence = round(best_score / 100.0, 2)
            self._log_mapping(raw_clean, best_match, entity_type, confidence, "FUZZY_RATIO_MATCH")
            return best_match, confidence, "FUZZY_RATIO_MATCH"

        # 3. Rule-Based Canonical Clean (If not in seed list, format cleanly)
        canonical_fallback = norm.title() if norm else raw_clean.title()
        # Clean specific trailing common artifacts
        canonical_fallback = re.sub(r'\s+', ' ', canonical_fallback).strip()
        self._log_mapping(raw_clean, canonical_fallback, entity_type, 0.85, "RULE_BASED_CLEAN")
        return canonical_fallback, 0.85, "RULE_BASED_CLEAN"

    def _log_mapping(self, raw: str, canonical: str, entity_type: str, confidence: float, method: str):
        """Append mapping record to internal audit log for Tab 6 export."""
        record = EntityMappingRecord(
            raw_name=raw,
            canonical_name=canonical,
            entity_type=entity_type,
            confidence=confidence,
            resolution_method=method,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.mapping_logs.append(record)

    def get_audit_logs(self) -> List[EntityMappingRecord]:
        """Retrieve deduplicated audit trail."""
        seen = set()
        deduped = []
        for r in self.mapping_logs:
            key = (r.raw_name, r.canonical_name, r.entity_type)
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        return deduped
