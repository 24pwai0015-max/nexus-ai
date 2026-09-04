import asyncio
import re
from typing import List, Dict, AsyncGenerator, Optional
from config import settings

SYSTEM_PROMPT = """You are Nexus AI, a cutting-edge multimodal intelligence system.
You provide insightful, accurate, and structured answers.

When real-time web search results are included in your context:
1. Ground your response strictly in the retrieved facts.
2. Provide source citations using bracketed numbers, e.g. [1], [2], matching the sources in the search context.
3. Be objective, concise, and highlight recent developments.

Always format your output using GitHub-flavored Markdown, including clear headings, bullet points, and code blocks where applicable.
"""

class LLMService:
    """
    LLM streaming client supporting any OpenAI-compatible provider (OpenAI, Groq, OpenRouter, DeepSeek, Ollama).
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not settings.has_openai_key:
            return None
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        return self._client

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        search_context: str = "",
        model: str = None
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        target_model = model or settings.DEFAULT_MODEL

        # Handle missing API key with an interactive onboarding stream
        if not client:
            user_last = messages[-1]["content"] if messages else ""
            mock_response = (
                f"### 🚀 Welcome to Nexus AI (Level 1 Gateway)\n\n"
                f"Your query was received: **\"{user_last}\"**\n\n"
                f"The **Intent Router**, **Live Web Search**, and **Image Generation** engines are online.\n\n"
                f"To connect live LLM reasoning (GPT-4o, DeepSeek, or Groq):\n"
                f"1. Open your `.env` file in `nexus ai/`.\n"
                f"2. Add your `OPENAI_API_KEY=your-key-here`.\n"
                f"3. Save the file and refresh!\n\n"
            )
            if search_context:
                mock_response += f"**Retrieved Real-Time Search Results:**\n{search_context}\n"

            for word in mock_response.split(" "):
                yield word + " "
                await asyncio.sleep(0.02)
            return

        # Prepare messages
        formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in messages[:-1]:
            formatted_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        # Inject search context into the latest user message if available
        last_message = messages[-1]["content"] if messages else ""
        if search_context:
            augmented_content = f"{search_context}\n\nUser Question: {last_message}"
        else:
            augmented_content = last_message

        formatted_messages.append({"role": "user", "content": augmented_content})

        try:
            stream = await client.chat.completions.create(
                model=target_model,
                messages=formatted_messages,
                stream=True,
                temperature=0.7
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n\n**[LLM Service Error]**: {str(e)}\nPlease check your API key and base URL in `.env`."

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        search_context: str = "",
        model: str = None
    ) -> str:
        """
        Non-streaming chat completion, returns full string response.
        """
        full_tokens = []
        async for chunk in self.stream_chat(messages, search_context=search_context, model=model):
            full_tokens.append(chunk)
        return "".join(full_tokens)

    async def generate_title(self, prompt: str) -> Optional[str]:
        """
        Uses LLM intelligence to craft a concise, conceptual 2-4 word conversation title.
        """
        client = self._get_client()
        if not client:
            return None
        try:
            resp = await client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[{
                    "role": "user",
                    "content": (
                        "Task: Generate a concise, intelligent 2 to 4 word topic title for a conversation starting with this user message.\n"
                        "Rules:\n"
                        "- If the message is a simple greeting (e.g. 'hi', 'hello', 'hey'), return 'Greeting Exchange' or 'Casual Greeting'.\n"
                        "- Do NOT use quotes, punctuation, markdown, or prefixes like 'Title:'.\n"
                        "- Capitalize words properly.\n"
                        "- Maximum 4 words.\n\n"
                        f"User message: {prompt}\nTitle:"
                    )
                }],
                max_tokens=20,
                temperature=0.3,
                stream=False
            )
            raw_title = resp.choices[0].message.content.strip().strip('"\'')
            raw_title = re.sub(r'^(?:Title|Topic):\s*', '', raw_title, flags=re.IGNORECASE)
            raw_title = raw_title.strip(' .!*#\n\r')
            if raw_title:
                words = raw_title.split()
                return " ".join(words[:4])
        except Exception:
            return None
        return None

llm_service = LLMService()
