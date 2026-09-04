import urllib.parse
import random
from typing import Dict, Any
from config import settings

class ImageService:
    """
    Image generation service supporting OpenAI DALL-E 3 and free high-quality FLUX/SDXL fallback.
    """

    async def generate(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        prompt = prompt.strip()
        
        # 1. Check if OpenAI DALL-E 3 is requested and configured (Groq keys do not support image generation)
        is_openai = settings.has_openai_key and not settings.OPENAI_API_KEY.startswith("gsk_")
        if settings.IMAGE_PROVIDER == "openai" or (settings.IMAGE_PROVIDER == "auto" and is_openai):
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                image_url = response.data[0].url
                revised_prompt = response.data[0].revised_prompt or prompt
                return {
                    "image_url": image_url,
                    "prompt": revised_prompt,
                    "provider": "openai:dall-e-3"
                }
            except Exception as e:
                print(f"[ImageService] OpenAI generation failed: {e}. Falling back to Pollinations FLUX.")

        # 2. Free high-tier fallback via Pollinations FLUX.1
        # Generates stunning photorealistic & artistic images with zero setup/key required
        seed = random.randint(10000, 999999)
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        
        return {
            "image_url": image_url,
            "prompt": prompt,
            "provider": "flux.1:pollinations"
        }

image_service = ImageService()
