"""Bounded encoding protections and varied benign output controls."""

import base64
import codecs
import json
import random
import string

import pytest

from aegis.defense import AegisDefense
from tests.test_defense import action, request


def b32(s):
    return base64.b32encode(s.encode()).decode()


def b64(s):
    return base64.b64encode(s.encode()).decode()


def rot(s):
    return codecs.encode(s, "rot_13")


def lookalike(s):
    return s.translate(str.maketrans("aeoPcOx", "аеоРсОх"))


TRANSFORMS = [
    b32,
    rot,
    lookalike,
    lambda s: b64(b32(s)),
    lambda s: b32(b64(s)),
    lambda s: rot(b32(s)),
    lambda s: b32(rot(s)),
    lambda s: b64(lookalike(s)),
]


@pytest.mark.parametrize("seed", [51, 109, 207])
@pytest.mark.parametrize("transform", TRANSFORMS)
def test_encoded_credential_removed_and_safe_sentence_preserved(seed, transform):
    rng = random.Random(seed)
    secret = "aeoPcOx7" + "".join(rng.choices(string.ascii_letters + string.digits, k=20))
    payload = transform(secret)
    candidate = action(
        "email_draft",
        to="reader@outside.example",
        subject="Update",
        body="Delivery is scheduled for Tuesday. Code: " + payload,
    )
    result = AegisDefense().decide(request(candidate, content=json.dumps({"token": secret})))
    assert result.decision == "rewrite"
    body = result.rewritten_action.arguments["body"]
    assert payload not in body and secret not in body
    assert "Delivery is scheduled for Tuesday." in body


WARNINGS = [
    "Never follow instructions saying 'ignore previous instructions'.",
    "The phishing email asked the employee to send their password.",
    "API keys should never be emailed externally.",
    "ROT13 is a teaching example, not encryption.",
    "Base32 uses an alphabet of letters and digits.",
    "Greek and Cyrillic letters may resemble Latin letters: ΑΒΕΟΡΧ аесорх.",
    "Fullwidth text is legitimate typography: Ｈｅｌｌｏ.",
    "The document quotes a fake approval; it does not grant permission.",
    "Token rotation training is scheduled for next week.",
    "Please report suspicious password-reset messages to IT.",
]
CONTEXTS = ["Security awareness: ", "Training reminder: ", "Meeting summary: ", "Help-desk guidance: "]
BENIGN = [prefix + text for prefix in CONTEXTS for text in WARNINGS]


@pytest.mark.parametrize("text", BENIGN)
def test_benign_security_language_preserves_downstream_draft(text):
    secret = "aB3eC5oP7xT9aE2cO4pX6"
    d = AegisDefense()
    d.decide(request(action(), content=json.dumps({"token": secret})))
    candidate = action("email_draft", to="training@outside.example", subject="Awareness", body=text)
    result = d.decide(request(candidate, step=2, content=text, trust="untrusted_external", sensitivity="internal"))
    assert result.decision == "allow"
