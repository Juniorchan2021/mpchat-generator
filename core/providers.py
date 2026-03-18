PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        "key_prefix": "AIzaSy...",
        "get_key_url": "https://aistudio.google.com/app/apikey",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4o-mini",
            "o3",
            "o4-mini",
            "gpt-4-turbo",
        ],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.openai.com/api-keys",
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "base_url": "https://api.anthropic.com",
        "models": [
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "claude-sonnet-4-20250514",
            "claude-3-5-haiku-20241022",
        ],
        "key_prefix": "sk-ant-...",
        "get_key_url": "https://console.anthropic.com/settings/keys",
        "sdk": "anthropic",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.deepseek.com/api_keys",
    },
    "kimi": {
        "label": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "models": [
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k",
            "moonshot-v1-auto",
        ],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.moonshot.cn/console/api-keys",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
        ],
        "key_prefix": "gsk_...",
        "get_key_url": "https://console.groq.com/keys",
    },
    "together": {
        "label": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Llama-3.1-8B-Instruct-Turbo",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ],
        "key_prefix": "...",
        "get_key_url": "https://api.together.ai/settings/api-keys",
    },
    "siliconflow": {
        "label": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen3-235B-A22B",
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "THUDM/glm-4-9b-chat",
        ],
        "key_prefix": "sk-...",
        "get_key_url": "https://cloud.siliconflow.cn/account/ak",
    },
    "zhipu": {
        "label": "Zhipu AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash", "glm-z1-plus"],
        "key_prefix": "...",
        "get_key_url": "https://open.bigmodel.cn/usercenter/apikeys",
    },
    "openrouter": {
        "label": "OpenRouter（支持全部模型）",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-opus-4-5",
            "anthropic/claude-sonnet-4-5",
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "openai/gpt-4.1",
            "openai/gpt-4o",
            "deepseek/deepseek-chat",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "key_prefix": "sk-or-...",
        "get_key_url": "https://openrouter.ai/keys",
    },
    "custom": {
        "label": "Custom（自定义）",
        "base_url": "",
        "models": [],
        "key_prefix": "",
        "get_key_url": "",
    },
}


def list_providers() -> list[dict]:
    items = []
    for provider_id, provider in PROVIDERS.items():
        items.append({"id": provider_id, **provider})
    return items
