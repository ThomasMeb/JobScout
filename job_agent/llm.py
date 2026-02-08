import logging

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
