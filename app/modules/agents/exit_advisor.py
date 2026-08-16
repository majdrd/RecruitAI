"""Conversation Exit Advisor: sklearn classifier plus a small keyword fallback."""

import re

import joblib

from app.modules.config import EXIT_MODEL_PATH

END_PATTERNS = [
    r"\bno longer interested\b",
    r"\bnot interested\b",
    r"\bremove me\b",
    r"\balready found a job\b",
    r"\balready hired\b",
    r"\bstop (texting|messaging|contacting)\b",
    r"\bunsubscribe\b",
    r"interview is confirmed",
    r"\bbooked the interview\b",
    r"\bslot is reserved\b",
    r"calendar invite",
]


def _keyword_decision(history_text):
    text = (history_text or "").lower()
    for pattern in END_PATTERNS:
        if re.search(pattern, text):
            return {
                "decision": "end",
                "reason": f"matched exit pattern: {pattern}",
                "source": "keywords",
            }
    return None


def load_model(path=EXIT_MODEL_PATH):
    if not path.exists():
        return None
    return joblib.load(path)


def predict(history_text):
    """Return {decision: end|dont_end, reason, source}."""
    keyword_hit = _keyword_decision(history_text)
    model = load_model()

    if model is None:
        if keyword_hit:
            return keyword_hit
        return {
            "decision": "dont_end",
            "reason": "no exit model found and no exit keywords",
            "source": "fallback",
        }

    label = model.predict([history_text or ""])[0]
    decision = "end" if label == "end" else "dont_end"
    result = {
        "decision": decision,
        "reason": f"classifier predicted {label}",
        "source": "sklearn",
    }

    # Keywords catch clear opt-outs the small model may miss.
    if keyword_hit and keyword_hit["decision"] == "end":
        result["decision"] = "end"
        result["reason"] = keyword_hit["reason"]
        result["source"] = "sklearn+keywords"
    return result


if __name__ == "__main__":
    samples = [
        "Candidate: Please remove me from your list. Thanks.",
        "Candidate: I have three years' experience with Django and Flask.",
    ]
    for sample in samples:
        print(sample)
        print(predict(sample))
        print()
