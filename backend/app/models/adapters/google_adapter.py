import time
import logging
from typing import Dict, Optional
import google.generativeai as genai
from app.models.adapters.base import ModelAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleAdapter(ModelAdapter):
    """Adapter for Google Gemini models."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or settings.GOOGLE_MODEL
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model,
            "model_type": self._infer_model_type(self.model),
            "vendor": "google",
        }

    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        """Generate response from Google Gemini model with retry logic."""
        if not self.api_key:
            raise ValueError("Google API key not configured")

        params = params or {}
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                start_time = time.time()

                model = genai.GenerativeModel(self.model)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": params.get("temperature", 0.7),
                        "max_output_tokens": params.get("max_tokens", 500),
                    },
                )

                response_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "response_text": response.text
                    if hasattr(response, "text")
                    else str(response),
                    "model_name": self.model,
                    "model_type": self._infer_model_type(self.model),
                    "vendor": "google",
                    "metadata": {
                        "tokens_used": 0,  # Gemini doesn't always return token counts
                        "response_time_ms": response_time_ms,
                        "model_version": self.model,
                    },
                }

            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
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
                    logger.error(f"Google API error: {str(e)}")
                    raise

        raise Exception("Max retries exceeded")
