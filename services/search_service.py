import asyncio
from typing import List, Dict, Any
import httpx
from config import settings

class SearchService:
    """
    Search service supporting Tavily API with zero-cost DuckDuckGo fallback.
    """

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        # 1. Attempt Tavily if key is configured
        if settings.has_tavily_key:
            try:
                results = await self._search_tavily(query, max_results)
                if results:
                    return results
            except Exception as e:
                print(f"[SearchService] Tavily search error: {e}, falling back to DuckDuckGo.")

        # 2. Free fallback to DuckDuckGo
        return await self._search_duckduckgo(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, str]]:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": max_results
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            clean_results = []
            for item in data.get("results", []):
                clean_results.append({
                    "title": item.get("title", "Untitled Source"),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })
            return clean_results

    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        def _ddg_sync():
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            results = []
            with DDGS(timeout=7) as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", "Web Result"),
                        "url": r.get("href", ""),
                        "content": r.get("body", "")
                    })
            return results

        try:
            return await asyncio.to_thread(_ddg_sync)
        except Exception as e:
            print(f"[SearchService] DuckDuckGo search error: {e}")
            return []

    def format_search_context(self, results: List[Dict[str, str]]) -> str:
        """
        Formats search results into an LLM-friendly context block with source indexes.
        """
        if not results:
            return ""

        lines = ["\n--- REAL-TIME WEB SEARCH RESULTS (Use these sources to ground your answer and cite using [1], [2], etc.) ---"]
        for idx, item in enumerate(results, start=1):
            lines.append(f"\n[{idx}] Title: {item['title']}")
            lines.append(f"URL: {item['url']}")
            lines.append(f"Snippet: {item['content']}")
        lines.append("\n--- END OF SEARCH RESULTS ---\n")
        return "\n".join(lines)

search_service = SearchService()
