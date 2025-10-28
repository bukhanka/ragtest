"""LLM service for interacting with language models."""
import logging
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLMs (OpenAI or local models)."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key or "dummy-key",
            base_url=settings.openai_base_url,
        )
        self.model = settings.openai_model
        logger.info(f"LLM service initialized with model: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get chat completion from LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        temperature: float = 0.7,
    ) -> tuple[str, Optional[Dict]]:
        """
        Generate completion with function calling support.
        
        Args:
            messages: Conversation messages
            tools: Available tools/functions
            temperature: Sampling temperature
            
        Returns:
            Tuple of (response_text, tool_call)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
            )
            
            choice = response.choices[0]
            message = choice.message
            
            # Check if tool was called
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                return message.content or "", {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "id": tool_call.id
                }
            
            return message.content, None
            
        except Exception as e:
            logger.error(f"Error in generate_with_tools: {e}")
            raise

