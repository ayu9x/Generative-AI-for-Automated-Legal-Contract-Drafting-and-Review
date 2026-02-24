"""Web Search Service - Internet-connected legal research using Google Custom Search and OpenAI."""

import json
import re
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger("legal_ai.web_search")


class WebSearchService:
    """Service for performing legal web searches and enriching AI analysis with internet data."""

    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.google_cx = settings.GOOGLE_SEARCH_CX
        self.enabled = settings.WEB_SEARCH_ENABLED
        self.max_results = settings.WEB_SEARCH_MAX_RESULTS

    @property
    def google_configured(self) -> bool:
        """Check if Google Custom Search is configured."""
        return bool(self.google_api_key and self.google_cx)

    async def search_google(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a Google Custom Search and return results."""
        if not self.google_configured:
            logger.warning("Google Search not configured, using fallback")
            return await self._fallback_search(query, num_results)

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": min(num_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": item.get("displayLink", ""),
                })
            return results
        except Exception as e:
            logger.error("Google Search failed", error=str(e))
            return await self._fallback_search(query, num_results)

    async def _fallback_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Fallback search using DuckDuckGo Instant Answer API (free, no key needed)."""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                data = response.json()

            results = []

            # Abstract text
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "snippet": data["AbstractText"][:500],
                    "url": data.get("AbstractURL", ""),
                    "source": data.get("AbstractSource", ""),
                })

            # Related topics
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "snippet": topic.get("Text", "")[:300],
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo",
                    })

            return results[:num_results]
        except Exception as e:
            logger.error("Fallback search failed", error=str(e))
            return []

    async def search_legal_info(self, query: str, jurisdiction: str = "US") -> Dict[str, Any]:
        """Search for legal information, regulations, and precedents."""
        legal_query = f"legal {query} {jurisdiction} law regulation"
        results = await self.search_google(legal_query, self.max_results)

        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "results": results,
            "result_count": len(results),
        }

    async def search_compliance_updates(
        self, regulation: str, jurisdiction: str = "US"
    ) -> Dict[str, Any]:
        """Search for latest compliance and regulatory updates."""
        query = f"{regulation} compliance update 2024 2025 {jurisdiction} regulation changes"
        results = await self.search_google(query, self.max_results)

        return {
            "regulation": regulation,
            "jurisdiction": jurisdiction,
            "updates": results,
            "update_count": len(results),
        }

    async def search_case_law(
        self, topic: str, jurisdiction: str = "US"
    ) -> Dict[str, Any]:
        """Search for relevant case law and legal precedents."""
        query = f"case law precedent {topic} {jurisdiction} court ruling"
        results = await self.search_google(query, self.max_results)

        return {
            "topic": topic,
            "jurisdiction": jurisdiction,
            "cases": results,
            "case_count": len(results),
        }

    async def get_enriched_context(
        self,
        contract_type: str,
        jurisdiction: str,
        topics: List[str],
    ) -> str:
        """Get enriched context from web search to feed into AI analysis."""
        all_results = []

        # Search for contract-type specific info
        type_results = await self.search_legal_info(
            f"{contract_type} contract requirements best practices", jurisdiction
        )
        all_results.extend(type_results.get("results", []))

        # Search for jurisdiction-specific requirements
        jurisdiction_results = await self.search_legal_info(
            f"{contract_type} legal requirements", jurisdiction
        )
        all_results.extend(jurisdiction_results.get("results", []))

        # Search for specific topics
        for topic in topics[:3]:  # Limit to 3 topics
            topic_results = await self.search_legal_info(topic, jurisdiction)
            all_results.extend(topic_results.get("results", []))

        # Format results as context for AI
        if not all_results:
            return "No additional web context available."

        context_parts = ["## Web Research Context\n"]
        seen_urls = set()
        for r in all_results:
            if r["url"] in seen_urls:
                continue
            seen_urls.add(r["url"])
            context_parts.append(f"**{r['title']}** ({r['source']})")
            context_parts.append(f"{r['snippet']}")
            context_parts.append(f"Source: {r['url']}\n")

        return "\n".join(context_parts[:30])  # Limit context size


# Singleton
web_search_service = WebSearchService()
