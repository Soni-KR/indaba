"""Source-derived DLP. No fixture values, canary markers, or scenario names."""

from __future__ import annotations

import base64
import json
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote

KEY = re.compile(r"(?:secret|token|credential|password|api.?key|iban|account.?number)", re.IGNORECASE)
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+./=-]{11,}")


def compact(text: str) -> str:
    return "".join(c.casefold() for c in unicodedata.normalize("NFKC", text) if c.isalnum())


def leaves(value, key=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, k)
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item, key)
    elif isinstance(value, str):
        yield key, value


@dataclass(frozen=True)
class Secret:
    value: str
    source: str
    sensitivity: str
    credential: bool


def extract_secrets(content: str, source: str, sensitivity: str) -> list[Secret]:
    try:
        pairs = list(leaves(json.loads(content)))
    except (ValueError, TypeError):
        pairs = [("", content)]
    found = {}
    for key, value in pairs:
        credential = bool(KEY.search(key))
        if credential and 8 <= len(value) <= 256:
            found[value] = Secret(value, source, sensitivity, True)
        if sensitivity in {"restricted", "confidential"}:
            for token in TOKEN.findall(value):
                # Long mixed identifiers; ordinary prose and tool names are not secrets.
                if any(c.isdigit() for c in token) and any(c.isalpha() for c in token):
                    found[token] = Secret(token, source, sensitivity, credential or sensitivity == "restricted")
            # Source-derived prose windows catch verbatim confidential copying as well as identifiers.
            if len(value) >= 60:
                for start in range(0, len(value) - 47, 24):
                    chunk = value[start : start + 48]
                    if len(compact(chunk)) >= 28:
                        found[chunk] = Secret(chunk, source, sensitivity, sensitivity == "restricted")
    return list(found.values())


def variants(value: str) -> list[tuple[str, str]]:
    raw = value.encode()
    return [
        ("plain", value),
        ("reversed", value[::-1]),
        ("base64", base64.b64encode(raw).decode()),
        ("base64url", base64.urlsafe_b64encode(raw).decode()),
        ("hex", raw.hex()),
    ]


def decoded_views(text: str):
    yield text
    current = {text}
    for _ in range(2):
        next_views = set()
        for item in current:
            decoded = unquote(item)
            if decoded != item:
                next_views.add(decoded)
            for token in re.findall(r"[A-Za-z0-9_+/=-]{16,}", item):
                try:
                    next_views.add(base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_").decode())
                except (ValueError, UnicodeError):
                    pass
                if len(token) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", token):
                    try:
                        next_views.add(bytes.fromhex(token).decode())
                    except (ValueError, UnicodeError):
                        pass
        yield from sorted(next_views)
        current = next_views


def matches(text: str, secrets: list[Secret]) -> list[tuple[Secret, str]]:
    views = [compact(v) for v in decoded_views(text)]
    result = []
    for secret in secrets:
        for encoding, value in variants(secret.value):
            needle = compact(value.rstrip("="))
            if len(needle) >= 8 and any(needle in view for view in views):
                result.append((secret, encoding))
                break
    return result


def redact(text: str, secrets: list[Secret]) -> str:
    result = text
    # Remove encoded envelopes while preserving surrounding useful prose.
    result = re.sub(
        r"[A-Za-z0-9_+/=%-]{16,}",
        lambda match: "[REDACTED]" if matches(match.group(), secrets) else match.group(),
        result,
    )
    for secret in secrets:
        for _, value in variants(secret.value):
            # Preserve surrounding prose; tolerate punctuation/whitespace insertion.
            chars = [re.escape(c) for c in value.rstrip("=") if c.isalnum()]
            if len(chars) >= 8:
                pattern = r"[\W_]*".join(chars)
                result = re.sub(pattern, "[REDACTED]", result, flags=re.IGNORECASE)
    if matches(result, secrets):
        return "[Sensitive content withheld; use a nonsensitive summary.]"
    return result


def egress_fields(action) -> dict[str, str]:
    """Public sink semantics; each destination field has its own output stream."""
    if action.type in {"respond", "memory_write"}:
        return {f"{action.type}:content": action.content or ""}
    if action.tool in {"email_draft", "email_send"}:
        destination = str(action.arguments.get("to", "")).strip().casefold()
        return {f"email:{destination}:{key}": str(action.arguments.get(key, "")) for key in ("subject", "body")}
    note_fields = {
        "case_note_create": ("case_id", ("text",)),
        "ticket_update": ("ticket_id", ("note",)),
        "incident_create": ("alert_id", ("title", "summary")),
        "incident_update": ("incident_id", ("note",)),
    }
    if action.tool in note_fields:
        identifier, fields = note_fields[action.tool]
        return {
            f"{action.tool}:{action.arguments.get(identifier)}:{key}": str(action.arguments.get(key) or "")
            for key in fields
        }
    return {}


def unordered_disclosures(previous, candidate, secrets, *, tiny_fragments=True):
    """Detect credential coverage by four-character windows or isolated two-character tokens.

    Fields are grouped by destination. This does not protect arbitrary single-character pieces,
    recipient collusion, custom ciphers, semantic leaks, or every partial disclosure.
    """
    for secret in secrets:
        # Restrict coverage heuristics to compact identifiers, not ordinary prose windows.
        if not secret.credential or not re.fullmatch(r"[A-Za-z0-9_+./=-]{12,128}", secret.value):
            continue
        for encoding, value in variants(secret.value):
            needle = compact(value.rstrip("="))
            if len(needle) < 16:
                continue
            groups = {}
            for sink, text in candidate.items():
                destination = sink.rsplit(":", 1)[0]
                groups.setdefault(destination, []).append(text)
            for destination, additions in groups.items():
                prior = [text for sink, text in previous.items() if sink.rsplit(":", 1)[0] == destination]

                def coverage(texts, needle=needle):
                    covered = set()
                    normalized = [compact(text) for text in texts]
                    pairs = {
                        compact(token)
                        for text in texts
                        for token in re.findall(r"(?<![A-Za-z0-9])[A-Za-z0-9]{2}(?![A-Za-z0-9])", text)
                    }
                    # Matching windows also covers longer pieces without concatenating unrelated fields.
                    for start in range(len(needle) - 3):
                        if any(needle[start : start + 4] in text for text in normalized):
                            covered.update(range(start, start + 4))
                    if tiny_fragments:
                        for start in range(len(needle) - 1):
                            if needle[start : start + 2] in pairs:
                                covered.update(range(start, start + 2))
                    return covered

                before = coverage(prior)
                after = before | coverage(additions)
                if len(after) > len(before) and len(after) >= max(16, int(len(needle) * 0.9 + 0.999)):
                    return secret, encoding, destination, len(after), len(needle)
    return None
