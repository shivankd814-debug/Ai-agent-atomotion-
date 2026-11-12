from app.providers import PROVIDERS

def test_supported_providers():
    assert PROVIDERS == {"gemini", "groq", "openrouter"}
