from app.schemas.billing import ModelInfo
from app.services.credits_service import CREDIT_RATES

# Static model catalog — will be dynamic via LiteLLM in the future
MODEL_CATALOG: list[ModelInfo] = [
    ModelInfo(
        id="deepseek-chat",
        name="DeepSeek V3",
        provider="DeepSeek",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["deepseek-chat"]["input"],
        credits_per_1k_output=CREDIT_RATES["deepseek-chat"]["output"],
        description="High performance, cost-effective general-purpose model",
    ),
    ModelInfo(
        id="deepseek-reasoner",
        name="DeepSeek R1",
        provider="DeepSeek",
        tier="premium",
        credits_per_1k_input=CREDIT_RATES["deepseek-reasoner"]["input"],
        credits_per_1k_output=CREDIT_RATES["deepseek-reasoner"]["output"],
        description="Advanced reasoning model for complex tasks",
    ),
    ModelInfo(
        id="qwen-turbo",
        name="Qwen Turbo",
        provider="Alibaba",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["qwen-turbo"]["input"],
        credits_per_1k_output=CREDIT_RATES["qwen-turbo"]["output"],
        description="Fast and affordable, great for everyday tasks",
    ),
    ModelInfo(
        id="qwen-plus",
        name="Qwen Plus",
        provider="Alibaba",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["qwen-plus"]["input"],
        credits_per_1k_output=CREDIT_RATES["qwen-plus"]["output"],
        description="Balanced performance and cost",
    ),
    ModelInfo(
        id="qwen-max",
        name="Qwen Max",
        provider="Alibaba",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["qwen-max"]["input"],
        credits_per_1k_output=CREDIT_RATES["qwen-max"]["output"],
        description="Alibaba's most capable model",
    ),
    ModelInfo(
        id="claude-sonnet",
        name="Claude Sonnet",
        provider="Anthropic",
        tier="premium",
        credits_per_1k_input=CREDIT_RATES["claude-sonnet"]["input"],
        credits_per_1k_output=CREDIT_RATES["claude-sonnet"]["output"],
        description="Top-tier reasoning and writing quality",
    ),
    ModelInfo(
        id="claude-haiku",
        name="Claude Haiku",
        provider="Anthropic",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["claude-haiku"]["input"],
        credits_per_1k_output=CREDIT_RATES["claude-haiku"]["output"],
        description="Fast and affordable Anthropic model",
    ),
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="OpenAI",
        tier="premium",
        credits_per_1k_input=CREDIT_RATES["gpt-4o"]["input"],
        credits_per_1k_output=CREDIT_RATES["gpt-4o"]["output"],
        description="OpenAI's flagship multimodal model",
    ),
    ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="OpenAI",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["gpt-4o-mini"]["input"],
        credits_per_1k_output=CREDIT_RATES["gpt-4o-mini"]["output"],
        description="Affordable and fast OpenAI model",
    ),
    ModelInfo(
        id="gemini-flash",
        name="Gemini Flash",
        provider="Google",
        tier="standard",
        credits_per_1k_input=CREDIT_RATES["gemini-flash"]["input"],
        credits_per_1k_output=CREDIT_RATES["gemini-flash"]["output"],
        description="Google's fast and efficient model",
    ),
]


def get_available_models() -> list[ModelInfo]:
    return MODEL_CATALOG
