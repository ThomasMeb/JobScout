"""LLM abstraction layer — multi-provider support (DeepSeek, OpenAI, Anthropic)."""

import logging
import os

import httpx
from openai import AsyncOpenAI

from job_agent.config import DEEPSEEK_API_KEY, load_config

logger = logging.getLogger(__name__)

# Pricing per million tokens
PRICING = {
    # DeepSeek
    "deepseek-chat": {"input": 0.28, "output": 1.10, "cache_hit": 0.028},
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    # Anthropic
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}


def _resolve_provider(model: str, cfg: dict) -> str:
    """Detect LLM provider from model name or explicit config."""
    # Explicit provider in config takes priority
    provider = cfg.get("llm", {}).get("provider", "").lower()
    if provider in ("deepseek", "openai", "anthropic"):
        return provider

    # Auto-detect from model name
    model_lower = model.lower()
    if "deepseek" in model_lower:
        return "deepseek"
    if "claude" in model_lower:
        return "anthropic"
    # Default: OpenAI-compatible
    return "openai"


def _get_api_key(provider: str) -> str:
    """Get the API key for the given provider."""
    if provider == "deepseek":
        return DEEPSEEK_API_KEY
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY", "")
    return os.environ.get("OPENAI_API_KEY", "")


def _get_base_url(provider: str, cfg: dict) -> str | None:
    """Get base URL — only needed for DeepSeek / custom endpoints."""
    if provider == "deepseek":
        return cfg.get("llm", {}).get("base_url", "https://api.deepseek.com")
    # For OpenAI: only use base_url if explicitly NOT DeepSeek's default
    # (avoids sending OpenAI calls to deepseek.com when user only changes model)
    base_url = cfg.get("llm", {}).get("base_url")
    if base_url and "deepseek" in base_url:
        return None
    return base_url


async def _call_openai_compatible(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    base_url: str | None,
) -> tuple[str, int, int]:
    """Call OpenAI-compatible API (DeepSeek, OpenAI)."""
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    client = AsyncOpenAI(**kwargs)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    text = response.choices[0].message.content or ""
    in_tok = response.usage.prompt_tokens if response.usage else 0
    out_tok = response.usage.completion_tokens if response.usage else 0
    return text, in_tok, out_tok


async def _call_anthropic(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
) -> tuple[str, int, int]:
    """Call Anthropic API (conditional import)."""
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "Package 'anthropic' is required for Claude models. "
            "Install it with: pip install anthropic>=0.40.0"
        )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text if response.content else ""
    in_tok = response.usage.input_tokens
    out_tok = response.usage.output_tokens
    return text, in_tok, out_tok


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> tuple[str, int, int]:
    """Call LLM and return (response_text, input_tokens, output_tokens).

    Provider is auto-detected from model name or explicit config.
    Signature unchanged for backward compatibility.
    """
    cfg = load_config()
    model = cfg["llm"]["model"]
    provider = _resolve_provider(model, cfg)
    api_key = _get_api_key(provider)

    if not api_key:
        raise ValueError(f"No API key found for provider '{provider}'. Check your .env file.")

    try:
        if provider == "anthropic":
            return await _call_anthropic(
                model, system_prompt, user_prompt, max_tokens, temperature, api_key,
            )
        else:
            base_url = _get_base_url(provider, cfg)
            return await _call_openai_compatible(
                model, system_prompt, user_prompt, max_tokens, temperature, api_key, base_url,
            )
    except Exception as e:
        logger.error(f"LLM call failed ({provider}/{model}): {e}")
        raise


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICING.get(model, PRICING["deepseek-chat"])
    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return round(cost, 6)


async def check_deepseek_balance() -> dict | None:
    """Query DeepSeek API for real account balance.

    Returns dict with keys: is_available, total_balance, currency
    or None if the request fails.
    """
    url = "https://api.deepseek.com/user/balance"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Find USD balance (fallback to first entry)
            for info in data.get("balance_infos", []):
                if info.get("currency") == "USD":
                    return {
                        "is_available": data.get("is_available", False),
                        "total_balance": float(info["total_balance"]),
                        "currency": "USD",
                    }
            # No USD entry, use first available
            if data.get("balance_infos"):
                info = data["balance_infos"][0]
                return {
                    "is_available": data.get("is_available", False),
                    "total_balance": float(info["total_balance"]),
                    "currency": info.get("currency", "???"),
                }
            return None
    except Exception as e:
        logger.warning(f"Failed to check DeepSeek balance: {e}")
        return None
