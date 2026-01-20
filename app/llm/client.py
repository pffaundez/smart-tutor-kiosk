import time
import requests


class LLMClient:
    """
    Minimal Ollama client using /api/chat.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "tinyllama:latest", timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> dict:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_tokens),
            },
        }

        t0 = time.perf_counter()
        r = requests.post(url, json=payload, timeout=self.timeout)
        latency_ms = (time.perf_counter() - t0) * 1000

        r.raise_for_status()
        data = r.json()

        text = data["message"]["content"]
        return {"text": text, "latency_ms": latency_ms, "raw": data}


