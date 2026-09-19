import json
from types import SimpleNamespace

import pytest
from sentinel.models.base import TurnHints
from sentinel.models.hf_adapter import HFModelAdapter

from aegis.local_model import LocalQwenAdapter


@pytest.mark.parametrize(
    "url", ["https://example.com", "http://192.168.1.1:8080", "http://localhost:8080", "http://user:pw@127.0.0.1"]
)
def test_runtime_rejects_non_loopback_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        LocalQwenAdapter(url)


def test_real_adapter_never_sends_reference_plans(monkeypatch):
    sent = []

    class Reply:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"type":"respond","content":"Done","final":true}'}}]}

    def post(url, **kwargs):
        sent.append(kwargs)
        return Reply()

    monkeypatch.setattr("aegis.local_model.httpx.post", post)
    model = LocalQwenAdapter()
    model.start_turn("Help the user", TurnHints(tools=[], reference_plan=("EVALUATOR_ONLY_SENTINEL",)))
    result = model.propose(SimpleNamespace(observations=[]))
    assert result.final
    assert "EVALUATOR_ONLY_SENTINEL" not in json.dumps(sent)
    assert sent[0]["trust_env"] is False


def test_stock_prompt_matches_updated_reference_without_loading_weights(monkeypatch):
    sent = []

    class Reply:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"type":"respond","content":"Done","final":true}'}}]}

    def post(url, **kwargs):
        sent.append(kwargs["json"])
        return Reply()

    monkeypatch.setattr("aegis.local_model.httpx.post", post)
    hints = TurnHints(tools=[{"name": "example", "description": "Read", "consequential": False,
                             "parameters": {"type": "object"}}], reference_plan=("NEVER_SEND",))
    context = SimpleNamespace(observations=[SimpleNamespace(kind="tool_result", text="Observed evidence")])
    local = LocalQwenAdapter()
    local.start_turn("Read evidence", hints)
    local.propose(context)
    # _messages is pure; bypass the constructor so this test needs no torch or model weights.
    reference = HFModelAdapter.__new__(HFModelAdapter)
    reference._max_context_chars = 12000
    reference.start_turn("Read evidence", hints)
    assert sent[0]["messages"] == reference._messages(context)
    assert sent[0]["max_tokens"] == 768
