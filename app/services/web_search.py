"""Web search service using DuckDuckGo."""
import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import asyncio

logger = logging.getLogger(__name__)


class WebSearchService:
    """Service for searching information on the web."""
    
    def __init__(self):
        """Initialize web search service."""
        self.ddgs = DDGS()
    
    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        try:
            logger.info(f"Searching web for: {query}")
            
            # DuckDuckGo search is synchronous, run in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=max_results))
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                })
            
            logger.info(f"Found {len(formatted_results)} web search results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}", exc_info=True)
            return []
    
    async def search_and_summarize(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """
        Search web and return formatted summary.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Formatted string with search results
        """
        results = await self.search(query, max_results)
        
        if not results:
            return "No search results found."
        
        # Format results as readable text
        summary = f"Web search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   {result['snippet']}\n"
            summary += f"   URL: {result['url']}\n\n"
        
        return summary

