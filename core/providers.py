PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"],
        "key_prefix": "AIzaSy...",
        "get_key_url": "https://aistudio.google.com/apikey",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.openai.com/api-keys",
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
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"],
        "key_prefix": "sk-...",
        "get_key_url": "https://platform.moonshot.cn/console/api-keys",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
            "deepseek/deepseek-chat",
        ],
        "key_prefix": "sk-or-...",
        "get_key_url": "https://openrouter.ai/keys",
    },
    "custom": {
        "label": "Custom",
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
