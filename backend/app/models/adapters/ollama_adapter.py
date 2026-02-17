import time
import logging
from typing import Dict, Optional
import httpx
from app.models.adapters.base import ModelAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaAdapter(ModelAdapter):
    """Adapter for local Ollama models."""

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = httpx.Client(timeout=30.0)

    def get_model_info(self) -> Dict[str, str]:
        return {"model_name": self.model, "model_type": "local", "vendor": "ollama"}

    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        """Generate response from local Ollama model."""
        params = params or {}
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                start_time = time.time()

                response = self.client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": params.get("temperature", 0.7),
                            "num_predict": params.get("max_tokens", 500),
                        },
                    },
                )
                response.raise_for_status()

                data = response.json()
                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "response_text": data.get("response", ""),
                    "model_name": self.model,
                    "model_type": "local",
                    "vendor": "ollama",
                    "metadata": {
                        "tokens_used": data.get("eval_count", 0)
                        + data.get("prompt_eval_count", 0),
                        "response_time_ms": response_time_ms,
                        "model_version": self.model,
                    },
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2**retry_count
                        logger.warning(
                            f"Rate limit hit, waiting {wait_time}s before retry {retry_count}"
                        )
                        time.sleep(wait_time)
                    else:
                        raise
                else:
                    logger.error(f"Ollama API error: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"Ollama API error: {str(e)}")
                raise

        raise Exception("Max retries exceeded")
