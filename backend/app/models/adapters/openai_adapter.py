import os
import time
import logging
from typing import Dict, Optional
import openai
from app.models.adapters.base import ModelAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI models."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or settings.OPENAI_MODEL
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None

    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model,
            "model_type": self._infer_model_type(self.model),
            "vendor": "openai",
        }

    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        """Generate response from OpenAI model with retry logic."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        params = params or {}
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                start_time = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=params.get("max_tokens", 500),
                    temperature=params.get("temperature", 0.7),
                    timeout=120,
                )

                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "response_text": response.choices[0].message.content,
                    "model_name": self.model,
                    "model_type": self._infer_model_type(self.model),
                    "vendor": "openai",
                    "metadata": {
                        "tokens_used": response.usage.total_tokens
                        if response.usage
                        else 0,
                        "response_time_ms": response_time_ms,
                        "model_version": response.model,
                    },
                }

            except openai.RateLimitError:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.warning(
                        f"Rate limit hit, waiting {wait_time}s before retry {retry_count}"
                    )
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise

        raise Exception("Max retries exceeded")
