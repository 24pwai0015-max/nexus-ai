import re
from enum import Enum
from typing import Tuple

class Intent(str, Enum):
    CHAT = "chat"
    SEARCH = "search"
    IMAGE = "image"

class IntentRouter:
    """
    High-speed intent router that classifies queries into:
    - IMAGE: Visual generation requests
    - SEARCH: Live web browsing, breaking news, or real-time fact retrieval
    - CHAT: General reasoning, coding, writing, and direct knowledge
    """

    IMAGE_PATTERNS = [
        r"\b(generate|create|make|draw|paint|render|produce|design)\b.*?\b(image|picture|photo|illustration|artwork|wallpaper|drawing|portrait|logo|graphic|visual)\b",
        r"\b(image|picture|photo|illustration|drawing|artwork)\s+(of|depicting|showing|with)\b",
        r"\bshow\s+me\s+a\s+(picture|photo|image|drawing)\b",
        r"^(draw|paint|illustrate)\s+",
        r"^image:\s*",
    ]

    SEARCH_PATTERNS = [
        r"\b(search|google|browse|look\s*up|find\s+info\s+on|check\s+online)\b",
        r"\b(latest|recent|today(?:'s)?|yesterday|this\s+(?:morning|afternoon|evening|week|month|year)|breaking|current|right\s+now|live\s+updates?)\b",
        r"\b(news|weather|stocks?|markets?|cryptocurrency|crypto|bitcoin|inflation|scores?)\b",
        r"\b(who\s+won|who\s+is\s+currently|what\s+happened|current\s+status\s+of)\b",
        r"\b(2025|2026)\b",  # Future/recent temporal queries
        r"^search:\s*",
    ]

    def __init__(self):
        self._image_regexes = [re.compile(p, re.IGNORECASE) for p in self.IMAGE_PATTERNS]
        self._search_regexes = [re.compile(p, re.IGNORECASE) for p in self.SEARCH_PATTERNS]

    def classify(self, query: str, explicit_mode: str = "auto") -> Tuple[Intent, str]:
        """
        Classifies user query and returns (Intent, cleaned_prompt/query).
        """
        cleaned = query.strip()
        
        # Respect explicit overrides from UI or API parameters
        if explicit_mode == "image":
            return Intent.IMAGE, self._clean_image_prefix(cleaned)
        elif explicit_mode == "search":
            return Intent.SEARCH, self._clean_search_prefix(cleaned)
        elif explicit_mode == "chat":
            return Intent.CHAT, cleaned

        # Check for explicit prefixes
        if cleaned.lower().startswith("image:"):
            return Intent.IMAGE, cleaned[6:].strip()
        if cleaned.lower().startswith("search:"):
            return Intent.SEARCH, cleaned[7:].strip()

        # Rule-based pattern checks
        for pattern in self._image_regexes:
            if pattern.search(cleaned):
                return Intent.IMAGE, cleaned

        for pattern in self._search_regexes:
            if pattern.search(cleaned):
                return Intent.SEARCH, cleaned

        return Intent.CHAT, cleaned

    def _clean_image_prefix(self, prompt: str) -> str:
        prompt = re.sub(r"^(generate|create|draw|make)\s+(an?\s+)?(image|picture|photo)\s+(of\s+)?", "", prompt, flags=re.IGNORECASE)
        return prompt.strip()

    def _clean_search_prefix(self, query: str) -> str:
        query = re.sub(r"^(search|lookup|google)\s+(for\s+)?", "", query, flags=re.IGNORECASE)
        return query.strip()

router = IntentRouter()
