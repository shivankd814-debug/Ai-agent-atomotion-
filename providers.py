from .config import get_settings

PROVIDERS = {"gemini", "groq", "openrouter"}

class ProviderError(RuntimeError):
    pass

def provider_status():
    s = get_settings()
    return {
        "gemini": {"configured": bool(s.gemini_api_key), "model": s.gemini_model, "base_url": "Google Gemini OpenAI-compatible API"},
        "groq": {"configured": bool(s.groq_api_key), "model": s.groq_model, "base_url": "Groq API"},
        "openrouter": {"configured": bool(s.openrouter_api_key), "model": s.openrouter_model, "base_url": "OpenRouter API"},
    }

def make_client(provider: str):
    from openai import AsyncOpenAI
    s = get_settings()
    if provider not in PROVIDERS:
        raise ProviderError("Unknown provider. Choose gemini, groq, or openrouter.")
    if provider == "gemini":
        key, model = s.gemini_api_key, s.gemini_model
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        headers = {}
    elif provider == "groq":
        key, model = s.groq_api_key, s.groq_model
        base_url = "https://api.groq.com/openai/v1"
        headers = {}
    else:
        key, model = s.openrouter_api_key, s.openrouter_model
        base_url = "https://openrouter.ai/api/v1"
        headers = {"HTTP-Referer": s.openrouter_site_url, "X-Title": s.openrouter_app_name}
    if not key:
        raise ProviderError(f"{provider.title()} API key is not configured. Add it to your server .env file, then restart.")
    if not model:
        raise ProviderError(f"No model configured for {provider}. Set its model in .env.")
    return AsyncOpenAI(api_key=key, base_url=base_url, default_headers=headers), model

async def ask(provider: str, system: str, user: str, temperature: float = 0.2) -> str:
    client, model = make_client(provider)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "The model returned an empty response."
    except Exception as exc:
        # Avoid echoing request headers or secrets in logs/messages.
        raise ProviderError(f"{provider.title()} request failed: {type(exc).__name__}: {str(exc)[:300]}") from None
    finally:
        await client.close()
