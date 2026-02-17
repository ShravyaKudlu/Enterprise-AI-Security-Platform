from abc import ABC, abstractmethod
from typing import Dict, Optional


class ModelAdapter(ABC):
    """Abstract base class for LLM model adapters."""

    @abstractmethod
    def generate(self, prompt: str, params: Optional[Dict] = None) -> Dict:
        """
        Generate a response from the model.

        Args:
            prompt: The input prompt
            params: Optional generation parameters

        Returns:
            Dict with standardized response format:
            {
                "response_text": str,
                "model_name": str,
                "model_type": "enterprise" | "public" | "local",
                "vendor": "openai" | "anthropic" | "google" | "ollama",
                "metadata": {
                    "tokens_used": int,
                    "response_time_ms": int,
                    "model_version": str
                }
            }
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """
        Return model information.

        Returns:
            Dict with keys: model_name, model_type, vendor
        """
        pass

    def _infer_model_type(self, model_name: str) -> str:
        """Infer model type from model name."""
        name_lower = model_name.lower()
        if "enterprise" in name_lower:
            return "enterprise"
        elif any(x in name_lower for x in ["llama", "mistral", "local"]):
            return "local"
        else:
            return "public"
