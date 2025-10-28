"""Main assistant agent with routing logic."""
import logging
import json
import uuid
from typing import List, Dict, Optional
from app.services.llm import LLMService
from app.services.rag import RAGService
from app.services.sql_agent import SQLAgent
from app.services.web_search import WebSearchService
from app.models import ChatResponse, ToolUsed

logger = logging.getLogger(__name__)


class AssistantAgent:
    """
    Main assistant agent that routes queries to appropriate tools.
    
    This agent analyzes user queries and decides which tool to use:
    - RAG for documentation questions
    - SQL for database queries
    - Web Search for current information
    """
    
    def __init__(self, rag_service: RAGService):
        """Initialize assistant agent."""
        self.llm_service = LLMService()
        self.rag_service = rag_service
        self.sql_agent = SQLAgent(self.llm_service)
        self.web_search = WebSearchService()
        
        # Initialize SQL agent
        import asyncio
        asyncio.create_task(self.sql_agent.initialize())
        
        # Conversation history storage (in-memory for MVP)
        self.conversations: Dict[str, List[Dict]] = {}
        
        logger.info("Assistant agent initialized")
    
    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        use_rag: bool = True,
        use_sql: bool = True,
        use_web_search: bool = True
    ) -> ChatResponse:
        """
        Process user message and generate response.
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID for context
            use_rag: Enable RAG tool
            use_sql: Enable SQL tool
            use_web_search: Enable web search tool
            
        Returns:
            ChatResponse with answer and metadata
        """
        try:
            # Generate or retrieve conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Get conversation history
            history = self.conversations.get(conversation_id, [])
            
            # Route query to appropriate tool(s)
            tool_results = await self._route_query(
                message,
                history,
                use_rag=use_rag,
                use_sql=use_sql,
                use_web_search=use_web_search
            )
            
            # Generate final response using tool results
            final_response = await self._generate_final_response(
                message,
                tool_results,
                history
            )
            
            # Update conversation history
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": final_response["response"]})
            self.conversations[conversation_id] = history[-10:]  # Keep last 10 messages
            
            # Create response
            return ChatResponse(
                response=final_response["response"],
                conversation_id=conversation_id,
                tools_used=final_response["tools_used"],
                sources=final_response["sources"]
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return ChatResponse(
                response=f"Извините, произошла ошибка при обработке запроса: {str(e)}",
                conversation_id=conversation_id or str(uuid.uuid4()),
                tools_used=[],
                sources=[]
            )
    
    async def _route_query(
        self,
        query: str,
        history: List[Dict],
        use_rag: bool,
        use_sql: bool,
        use_web_search: bool
    ) -> Dict:
        """
        Route query to appropriate tools using LLM reasoning.
        
        Returns:
            Dictionary with results from each tool
        """
        # Determine which tools to use
        routing_decision = await self._decide_tools(
            query,
            use_rag=use_rag,
            use_sql=use_sql,
            use_web_search=use_web_search
        )
        
        logger.info(f"Routing decision: {routing_decision}")
        
        results = {
            "rag": None,
            "sql": None,
            "web_search": None
        }
        
        # Execute RAG if needed
        if routing_decision.get("use_rag", False):
            try:
                rag_results = await self.rag_service.search(query, k=3)
                if rag_results:
                    results["rag"] = {
                        "success": True,
                        "documents": rag_results,
                        "summary": self._format_rag_results(rag_results)
                    }
            except Exception as e:
                logger.error(f"RAG error: {e}")
                results["rag"] = {"success": False, "error": str(e)}
        
        # Execute SQL if needed
        if routing_decision.get("use_sql", False):
            try:
                sql_result = await self.sql_agent.query(query)
                results["sql"] = sql_result
            except Exception as e:
                logger.error(f"SQL error: {e}")
                results["sql"] = {"success": False, "error": str(e)}
        
        # Execute web search if needed
        if routing_decision.get("use_web_search", False):
            try:
                search_results = await self.web_search.search(query, max_results=3)
                if search_results:
                    results["web_search"] = {
                        "success": True,
                        "results": search_results,
                        "summary": self._format_web_results(search_results)
                    }
            except Exception as e:
                logger.error(f"Web search error: {e}")
                results["web_search"] = {"success": False, "error": str(e)}
        
        return results
    
    async def _decide_tools(
        self,
        query: str,
        use_rag: bool,
        use_sql: bool,
        use_web_search: bool
    ) -> Dict[str, bool]:
        """
        Decide which tools to use for the query.
        
        Uses LLM to analyze the query and determine appropriate tools.
        """
        available_tools = []
        if use_rag:
            available_tools.append("RAG (documentation search)")
        if use_sql:
            available_tools.append("SQL (database queries about team and projects)")
        if use_web_search:
            available_tools.append("Web Search (current information from internet)")
        
        if not available_tools:
            return {"use_rag": False, "use_sql": False, "use_web_search": False}
        
        prompt = f"""Analyze the following user query and decide which tools should be used to answer it.

Available tools:
{', '.join(available_tools)}

Guidelines:
- Use RAG for questions about documentation, technical concepts, or product features
- Use SQL for questions about team members, projects, or organizational data
- Use Web Search for current events, recent information, or general knowledge not in documentation
- Multiple tools can be used simultaneously if needed

User query: "{query}"

Respond with a JSON object indicating which tools to use:
{{"use_rag": true/false, "use_sql": true/false, "use_web_search": true/false, "reasoning": "brief explanation"}}
"""
        
        messages = [
            {"role": "system", "content": "You are an intelligent routing assistant that decides which tools to use for queries."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=200
            )
            
            # Extract JSON from response
            decision = self._extract_json(response)
            logger.info(f"Tool routing reasoning: {decision.get('reasoning', 'N/A')}")
            
            return {
                "use_rag": decision.get("use_rag", False) and use_rag,
                "use_sql": decision.get("use_sql", False) and use_sql,
                "use_web_search": decision.get("use_web_search", False) and use_web_search
            }
            
        except Exception as e:
            logger.error(f"Error in tool routing: {e}")
            # Fallback: use heuristics
            query_lower = query.lower()
            
            # Simple keyword-based routing as fallback
            use_rag_fallback = any(word in query_lower for word in [
                'документация', 'как работает', 'что такое', 'объясни', 'инструкция'
            ]) and use_rag
            
            use_sql_fallback = any(word in query_lower for word in [
                'команда', 'сотрудник', 'проект', 'кто', 'список', 'разработчик'
            ]) and use_sql
            
            use_web_fallback = any(word in query_lower for word in [
                'найди в интернете', 'поищи', 'актуальн', 'новост', 'последн'
            ]) and use_web_search
            
            # If no tool matched, use RAG as default
            if not any([use_rag_fallback, use_sql_fallback, use_web_fallback]):
                use_rag_fallback = use_rag
            
            return {
                "use_rag": use_rag_fallback,
                "use_sql": use_sql_fallback,
                "use_web_search": use_web_fallback
            }
    
    async def _generate_final_response(
        self,
        query: str,
        tool_results: Dict,
        history: List[Dict]
    ) -> Dict:
        """Generate final response using tool results."""
        # Prepare context from tool results
        context_parts = []
        tools_used = []
        sources = []
        
        # Add RAG results
        if tool_results.get("rag") and tool_results["rag"].get("success"):
            context_parts.append("=== Documentation ===\n" + tool_results["rag"]["summary"])
            tools_used.append(ToolUsed(
                name="RAG",
                description="Retrieved information from documentation",
                result_summary=f"Found {len(tool_results['rag']['documents'])} relevant documents"
            ))
            sources.extend([doc["metadata"].get("source", "unknown") for doc in tool_results["rag"]["documents"]])
        
        # Add SQL results
        if tool_results.get("sql") and tool_results["sql"].get("success"):
            sql_data = tool_results["sql"]
            context_parts.append(f"=== Database Query Results ===\n"
                               f"SQL: {sql_data['sql_query']}\n"
                               f"Results: {json.dumps(sql_data['results'], ensure_ascii=False, indent=2)}")
            tools_used.append(ToolUsed(
                name="SQL",
                description="Queried database",
                result_summary=f"Retrieved {sql_data['row_count']} rows"
            ))
            sources.append("Internal Database")
        
        # Add web search results
        if tool_results.get("web_search") and tool_results["web_search"].get("success"):
            context_parts.append("=== Web Search Results ===\n" + tool_results["web_search"]["summary"])
            tools_used.append(ToolUsed(
                name="Web Search",
                description="Searched the internet",
                result_summary=f"Found {len(tool_results['web_search']['results'])} results"
            ))
            sources.extend([r["url"] for r in tool_results["web_search"]["results"]])
        
        # Generate response
        if context_parts:
            context = "\n\n".join(context_parts)
            system_prompt = """You are a helpful assistant. Use the provided context to answer the user's question.
Be accurate, concise, and cite sources when appropriate. If the context doesn't contain relevant information, say so.
Answer in Russian if the question is in Russian."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"}
            ]
        else:
            # No tools were used, generate general response
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer questions accurately and helpfully in Russian if the question is in Russian."},
                {"role": "user", "content": query}
            ]
        
        # Add conversation history
        messages = history[-4:] + messages if history else messages
        
        response = await self.llm_service.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            "response": response,
            "tools_used": tools_used,
            "sources": list(set(sources))  # Remove duplicates
        }
    
    def _format_rag_results(self, results: List[Dict]) -> str:
        """Format RAG results as text."""
        formatted = ""
        for i, result in enumerate(results, 1):
            formatted += f"Document {i} (score: {result['score']:.2f}):\n"
            formatted += f"{result['content']}\n"
            formatted += f"Source: {result['metadata'].get('source', 'unknown')}\n\n"
        return formatted
    
    def _format_web_results(self, results: List[Dict]) -> str:
        """Format web search results as text."""
        formatted = ""
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   {result['snippet']}\n"
            formatted += f"   {result['url']}\n\n"
        return formatted
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        try:
            # Try to parse as JSON directly
            return json.loads(text)
        except:
            # Try to find JSON in text
            import re
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("No valid JSON found in response")

