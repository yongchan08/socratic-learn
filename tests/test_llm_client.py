from types import SimpleNamespace

import pytest

from socratic_tutor import llm_client


class FakeOpenAI:
    kwargs = None

    def __init__(self, **kwargs):
        type(self).kwargs = kwargs


def test_llm_client_sets_explicit_connection_and_response_timeouts(monkeypatch):
    monkeypatch.setattr(llm_client, "OpenAI", FakeOpenAI)

    llm_client.LLMClient(model="test-model", api_key="test-key")

    timeout = FakeOpenAI.kwargs["timeout"]
    assert timeout.connect == 10.0
    assert timeout.read == 70.0
    assert FakeOpenAI.kwargs["max_retries"] == 1


class SequenceCompletions:
    def __init__(self, contents):
        self.contents = iter(contents)
        self.call_count = 0

    def create(self, **kwargs):
        self.call_count += 1
        self.last_kwargs = kwargs
        content = next(self.contents)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def test_complete_json_repairs_invalid_json_once():
    completions = SequenceCompletions(["not-json", '{"concepts": []}'])
    client = llm_client.LLMClient.__new__(llm_client.LLMClient)
    client.model = "test-model"
    client.temperature = 0.2
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = client.complete_json("system", "user")

    assert result == {"concepts": []}
    assert completions.call_count == 2


def test_complete_json_omits_temperature_for_gpt_5_models():
    completions = SequenceCompletions(['{"concepts": []}'])
    client = llm_client.LLMClient.__new__(llm_client.LLMClient)
    client.model = "gpt-5-mini"
    client.temperature = 0.2
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    client.complete_json("system", "user")

    assert "temperature" not in completions.last_kwargs


def test_complete_json_stops_after_one_json_repair():
    completions = SequenceCompletions(["bad-json", "still-bad"])
    client = llm_client.LLMClient.__new__(llm_client.LLMClient)
    client.model = "test-model"
    client.temperature = 0.2
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    with pytest.raises(llm_client.LLMJSONParseError):
        client.complete_json("system", "user")

    assert completions.call_count == 2
