import time
import logging
from typing import Dict, Optional
import anthropic
from app.models.adapters.base import ModelAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or settings.ANTHROPIC_MODEL
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = (
            anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        )

    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model,
            "model_type": self._infer_model_type(self.model),
            "vendor": "anthropic",
        }

    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        """Generate response from Anthropic model with retry logic."""
        if not self.client:
            raise ValueError("Anthropic API key not configured")

        params = params or {}
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                start_time = time.time()

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=params.get("max_tokens", 500),
                    temperature=params.get("temperature", 0.7),
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30,
                )

                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "response_text": response.content[0].text
                    if response.content
                    else "",
                    "model_name": self.model,
                    "model_type": self._infer_model_type(self.model),
                    "vendor": "anthropic",
                    "metadata": {
                        "tokens_used": response.usage.input_tokens
                        + response.usage.output_tokens
                        if response.usage
                        else 0,
                        "response_time_ms": response_time_ms,
                        "model_version": self.model,
                    },
                }

            except anthropic.RateLimitError:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2**retry_count
                    logger.warning(
                        f"Rate limit hit, waiting {wait_time}s before retry {retry_count}"
                    )
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                logger.error(f"Anthropic API error: {str(e)}")
                raise

        raise Exception("Max retries exceeded")
