"""Test LLM client."""
import pytest

from intel_engine.llm.client import LLMClient, LLMProvider


def test_llm_config_raises_on_missing_env_vars(monkeypatch):
    monkeypatch.delenv("LLM_MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MINIMAX_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MINIMAX_MODEL", raising=False)
    from intel_engine.settings import llm_config

    with pytest.raises(ValueError, match="Missing LLM config"):
        llm_config("minimax")


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


async def test_complete_json_strips_markdown_fences(monkeypatch, httpx_mock):
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "https://test.minimax.local/v1")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "test-model")

    httpx_mock.add_response(
        url="https://test.minimax.local/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": '```json\n{"answer": "yes"}\n```'}}
            ]
        },
    )

    client = LLMClient(provider=LLMProvider.minimax)
    result = await client.complete_json(system="You are a helper.", user="Is the sky blue?")
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
