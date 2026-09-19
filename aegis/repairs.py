"""Narrow, auditable repairs using public schemas and observed tool receipts."""

import re


def repair_read_arguments(action, tool):
    """Rename only documented-equivalent read fields; never infer an ID or repair a write."""
    if tool.capabilities != frozenset({"read"}):
        return None
    fields = tool.args_model.model_fields
    aliases = {"document_id": "doc_id", "keywords": "query", "search_query": "query"}
    args = dict(action.arguments)
    changed = []
    for old, new in aliases.items():
        if old in args and old not in fields and new in fields and new not in args:
            args[new] = args.pop(old)
            changed.append(f"{old}->{new}")
    if not changed:
        return None
    try:
        tool.args_model.model_validate(args)
    except ValueError:
        return None
    return action.model_copy(update={"arguments": args}), changed


CLAIMS = {
    "draft": re.compile(
        r"\b(?:draft(?: email)?(?: has been| was| is)? (?:prepared|created|saved)|"
        r"I (?:have )?(?:prepared|created|saved) (?:an? |the )?(?:email )?draft)\b",
        re.IGNORECASE,
    ),
    "incident": re.compile(
        r"\b(?:incident(?: ticket)?(?: has been| was| is)? (?:opened|created)|"
        r"I (?:have )?(?:opened|created) (?:an? |the )?incident)\b",
        re.IGNORECASE,
    ),
    "sent": re.compile(
        r"\b(?:(?:email|message)(?: has been| was| is) sent|"
        r"I (?:have )?sent (?:an? |the )?(?:email|message))\b",
        re.IGNORECASE,
    ),
}


def qualify_completion(text, receipts):
    """Qualify unsupported assertions; never manufacture an effect or claim full semantic coverage."""
    unsupported = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    for sentence in sentences:
        missing = [kind for kind, pattern in CLAIMS.items() if kind not in receipts and pattern.search(sentence)]
        if missing:
            unsupported.extend(missing)
            result.append("[Completion unverified: no successful " + ", ".join(missing) + " receipt observed.]")
        else:
            result.append(sentence)
    return " ".join(result), sorted(set(unsupported))
