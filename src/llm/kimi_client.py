from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"


class KimiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("KIMI_API_KEY", "")
        self.base_url = base_url or os.getenv("KIMI_BASE_URL", DEFAULT_BASE_URL)

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("KIMI_API_KEY is not set")
        payload: Dict[str, Any] = {
            "model": "moonshot-v1-8k",
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(f"Kimi API error: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Kimi API connection error: {exc}") from exc
