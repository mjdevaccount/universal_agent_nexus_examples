"""Model configuration and resolution utilities."""

import os
from enum import Enum
from typing import Optional, Tuple


class ModelProvider(Enum):
    """Available model providers."""

    OPENAI = "openai"
    LOCAL = "local"
    AUTO = "auto"


class ModelConfig:
    """Resolve model names consistently across examples."""

    MODEL_MAPPING = {
        "qwen2.5-32b": "qwen3",
        "qwen2.5-coder:14b": "qwen3",
        "qwen2.5": "qwen3",
        "gemma:2b-instruct": "qwen3",
    }

    MODEL_COMPLEXITY = {
        "qwen3": 32,
        "qwen2.5-coder:14b": 14,
        "gemma:2b-instruct": 2,
    }

    @staticmethod
    def resolve_model(model_name: Optional[str] = None, provider: ModelProvider = ModelProvider.AUTO) -> Tuple[str, ModelProvider]:
        """Resolve the configured model and provider."""

        env_model = os.getenv("UAA_MODEL")
        if env_model:
            return ModelConfig._process_model(env_model, provider)

        model = model_name or "qwen3"
        return ModelConfig._process_model(model, provider)

    @staticmethod
    def _process_model(model: str, provider: ModelProvider) -> Tuple[str, ModelProvider]:
        resolved_provider = provider
        model_value = model

        if model_value.startswith("local://"):
            model_value = model_value.replace("local://", "", 1)
            resolved_provider = ModelProvider.LOCAL
        elif model_value.startswith("gpt-"):
            resolved_provider = ModelProvider.OPENAI
        elif resolved_provider == ModelProvider.AUTO:
            resolved_provider = ModelProvider.LOCAL

        normalized = ModelConfig.MODEL_MAPPING.get(model_value, model_value)
        return normalized, resolved_provider

    @staticmethod
    def get_complexity_tier(model_name: str) -> int:
        """Return the recommended parameter size (in billions)."""

        normalized, _ = ModelConfig.resolve_model(model_name)
        return ModelConfig.MODEL_COMPLEXITY.get(normalized, 7)

    @staticmethod
    def is_local_model(model_name: Optional[str] = None) -> bool:
        """Check if the resolved provider is local."""

        _, provider = ModelConfig.resolve_model(model_name)
        return provider == ModelProvider.LOCAL

    @staticmethod
    def supports_tool_calling(model_name: Optional[str] = None) -> bool:
        """Determine if the model supports tool calling."""

        normalized_model, provider = ModelConfig.resolve_model(model_name)

        if provider == ModelProvider.OPENAI:
            return normalized_model.startswith("gpt-4") or normalized_model.startswith("gpt-4o")

        return "qwen" in normalized_model.lower()


__all__ = [
    "ModelConfig",
    "ModelProvider",
]
