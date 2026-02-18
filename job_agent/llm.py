import logging

import httpx
from openai import AsyncOpenAI

from job_agent.config import DEEPSEEK_API_KEY, load_config

logger = logging.getLogger(__name__)

# DeepSeek pricing (per million tokens)
PRICING = {
    "deepseek-chat": {"input": 0.28, "output": 1.10, "cache_hit": 0.028},
}


def get_client() -> AsyncOpenAI:
    cfg = load_config()
    return AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=cfg["llm"]["base_url"],
    )


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> tuple[str, int, int]:
    """Call DeepSeek and return (response_text, input_tokens, output_tokens)."""
    cfg = load_config()
    model = cfg["llm"]["model"]
    client = get_client()

    try:
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
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        return text, input_tokens, output_tokens
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
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
