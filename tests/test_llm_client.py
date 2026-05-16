"""Test LLM client."""
from intel_engine.llm.client import LLMClient, LLMProvider


async def test_client_calls_correct_endpoint(monkeypatch, httpx_mock):
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "https://test.minimax.local/v1")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "test-model")

    httpx_mock.add_response(
        url="https://test.minimax.local/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": '{"answer": "yes"}'}}
            ]
        },
    )

    client = LLMClient(provider=LLMProvider.minimax)
    result = await client.complete_json(
        system="You are a helper.",
        user="Is the sky blue?",
    )
    assert result == {"answer": "yes"}


async def test_client_returns_plain_text(monkeypatch, httpx_mock):
    monkeypatch.setenv("LLM_KIMI_BASE_URL", "https://test.kimi.local/v1")
    monkeypatch.setenv("LLM_KIMI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_KIMI_MODEL", "test-model")

    httpx_mock.add_response(
        url="https://test.kimi.local/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": "Hello, world."}}
            ]
        },
    )

    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_text(system="You are a helper.", user="Say hi")
    assert result == "Hello, world."
