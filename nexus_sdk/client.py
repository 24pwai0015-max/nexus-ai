import json
from typing import List, Dict, Any, Optional, Iterator, Union
import httpx

class NexusAPIError(Exception):
    """Raised when the Nexus API returns an error response."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"NexusAPIError [HTTP {status_code}]: {message}")

class ChatNamespace:
    def __init__(self, client: "NexusClient"):
        self._client = client

    def create(
        self,
        messages: List[Dict[str, str]],
        model: str = "nexus-omni-1",
        mode: str = "auto",
        stream: bool = False,
        temperature: float = 0.7
    ) -> Union[Dict[str, Any], Iterator[str]]:
        """
        Creates a multimodal chat completion.
        If stream=True, returns a generator yielding text chunks.
        If stream=False, returns the complete response dictionary.
        """
        payload = {
            "messages": messages,
            "model": model,
            "mode": mode,
            "stream": stream,
            "temperature": temperature
        }

        if not stream:
            return self._client._post("/chat/completions", payload)

        # Handle streaming
        return self._stream_chat(payload)

    def _stream_chat(self, payload: Dict[str, Any]) -> Iterator[str]:
        headers = self._client._headers()
        url = f"{self._client.base_url}/chat/completions"

        with httpx.Client(timeout=60.0) as http:
            with http.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    raise NexusAPIError(response.status_code, response.read().decode())

                for line in response.iter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

class SearchNamespace:
    def __init__(self, client: "NexusClient"):
        self._client = client

    def query(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Queries live web search directly. Returns verified sources and snippets.
        """
        return self._client._post("/search", {"query": query, "max_results": max_results})

class ImagesNamespace:
    def __init__(self, client: "NexusClient"):
        self._client = client

    def generate(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """
        Generates visual assets via FLUX or DALL-E.
        """
        return self._client._post("/images/generations", {"prompt": prompt, "size": size})

class RouteNamespace:
    def __init__(self, client: "NexusClient"):
        self._client = client

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classifies query intent into CHAT, SEARCH, or IMAGE.
        """
        return self._client._post("/route", {"text": text})

class NexusClient:
    """
    Official Python Client for the Nexus AI Platform.
    """
    def __init__(self, api_key: str = "nexus_dev_master_key", base_url: str = "http://127.0.0.1:8000/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        
        # Sub-namespaces
        self.chat = ChatNamespace(self)
        self.search = SearchNamespace(self)
        self.images = ImagesNamespace(self)
        self.route = RouteNamespace(self)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _post(self, path: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=30.0) as http:
            response = http.post(url, json=json_data, headers=self._headers())
            if response.status_code >= 400:
                raise NexusAPIError(response.status_code, response.text)
            return response.json()

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=15.0) as http:
            response = http.get(url, headers=self._headers())
            if response.status_code >= 400:
                raise NexusAPIError(response.status_code, response.text)
            return response.json()

    def models(self) -> List[Dict[str, Any]]:
        """Lists available virtual models in the Nexus platform."""
        res = self._get("/models")
        return res.get("data", [])

    def usage(self) -> Dict[str, Any]:
        """Retrieves real-time usage metrics and request counts."""
        return self._get("/usage")
