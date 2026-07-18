from __future__ import annotations


def baseline_demo(text: str) -> str:
    return f"I hear you. I can help you think through the situation and identify a practical next step."


def controlled_demo(text: str, directives: list[str]) -> str:
    parts: list[str] = []
    if "increase_reassurance" in directives:
        parts.append("That sounds like a lot to carry right now.")
    if "suggest_immediate_human_support" in directives:
        parts.append("Please contact someone you trust or local emergency/crisis support now; if you are in immediate danger, call local emergency services.")
    elif "suggest_human_support" in directives:
        parts.append("It may help to include someone you trust outside this chat.")
    if "return_decision_to_user" in directives:
        parts.append("I should not make the final decision for you. We can narrow it to two or three options and you can choose the next step.")
    if "require_confirmation" in directives:
        parts.append("Before making an irreversible move, can we pause and confirm what needs to happen today versus what can wait?")
    if "block_exclusive_language" in directives:
        parts.append("I can listen, but I should not replace the people and support available in your life.")
    if not parts:
        parts.append("I can help you organize the options and think through the trade-offs.")
    return " ".join(parts)
