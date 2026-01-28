"""
LLM Client - Unified interface for OpenAI and Anthropic.
"""

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from src.core import get_settings, get_logger


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_model = settings.llm_model
        self.embedding_model = settings.embedding_model
        self.log = get_logger("llm.openai")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """Send chat completion request to OpenAI."""
        model = model or self.default_model

        self.log.debug(
            "chat_request",
            model=model,
            messages_count=len(messages),
        )

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content or ""

            self.log.info(
                "chat_response",
                model=model,
                tokens_prompt=response.usage.prompt_tokens if response.usage else 0,
                tokens_completion=response.usage.completion_tokens if response.usage else 0,
            )

            return content

        except Exception as e:
            self.log.error("chat_error", error=str(e))
            raise

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
    ) -> dict:
        """Send chat request and parse JSON response."""
        response = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.log.error("json_parse_error", response=response[:200], error=str(e))
            raise ValueError(f"Failed to parse JSON response: {e}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        self.log.debug("embed_request", texts_count=len(texts))

        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )

            embeddings = [item.embedding for item in response.data]

            self.log.info(
                "embed_response",
                texts_count=len(texts),
                dimensions=len(embeddings[0]) if embeddings else 0,
            )

            return embeddings

        except Exception as e:
            self.log.error("embed_error", error=str(e))
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.default_model = "claude-3-5-sonnet-20241022"
        self.log = get_logger("llm.anthropic")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """Send chat completion request to Anthropic."""
        model = model or self.default_model

        # Extract system message if present
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        self.log.debug(
            "chat_request",
            model=model,
            messages_count=len(chat_messages),
        )

        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=chat_messages,
            )

            content = response.content[0].text if response.content else ""

            self.log.info(
                "chat_response",
                model=model,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
            )

            return content

        except Exception as e:
            self.log.error("chat_error", error=str(e))
            raise

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Anthropic doesn't have embeddings - use OpenAI fallback."""
        raise NotImplementedError("Use OpenAI for embeddings")


class LLMClient:
    """
    Unified LLM client that can switch between providers.

    Usage:
        client = LLMClient()
        response = await client.chat([{"role": "user", "content": "Hello"}])
    """

    def __init__(self, provider: str = "openai"):
        if provider == "openai":
            self._client = OpenAIClient()
        elif provider == "anthropic":
            self._client = AnthropicClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self.provider = provider

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send chat completion request."""
        return await self._client.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> dict:
        """Send chat request and parse JSON response (OpenAI only)."""
        if isinstance(self._client, OpenAIClient):
            return await self._client.chat_json(messages, model)
        else:
            # Fallback for Anthropic - parse manually
            response = await self._client.chat(messages, model)
            return json.loads(response)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings."""
        if isinstance(self._client, AnthropicClient):
            # Fallback to OpenAI for embeddings
            openai_client = OpenAIClient()
            return await openai_client.embed(texts)
        return await self._client.embed(texts)
