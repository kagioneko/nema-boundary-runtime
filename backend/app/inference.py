from __future__ import annotations
import re
from .models import ControlState, SupportEscalation

def _has(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

def infer_demo_state(text: str) -> ControlState:
    """Transparent offline fallback for repeatable demos; not a classifier."""
    low_stakes = _has(text, [r"旅行", r"夕食", r"献立", r"映画", r"色を選", r"コード", r"Python"])
    dependency = _has(text, [r"全部.*決め", r"代わりに.*決", r"最終判断.*任せ", r"decide everything", r"can't decide"]) and not low_stakes
    exclusive = _has(text, [r"あなたしか", r"君しか", r"離れないで", r"ずっと一緒", r"私だけを見て", r"only one who understands", r"only need you"]) and not low_stakes
    immediate = _has(text, [r"今すぐ", r"直ちに", r"すぐに", r"今日この場", r"right now", r"immediately"])
    consequential = _has(text, [r"会社.*辞", r"退職", r"学校.*辞", r"関係.*終", r"契約.*解約", r"家を出", r"全部.*消", r"quit my (job|school)"])
    urgent = immediate and consequential
    distressed = _has(text, [r"意味がない", r"疲れた", r"どうでもいい", r"限界", r"希望がない", r"hopeless", r"exhausted"])
    high_support = _has(text, [r"死にたい", r"自殺", r"自分を傷つけ", r"kill myself", r"suicide", r"self-harm"])
    evidence: dict[str, str] = {}
    if dependency: evidence["decision_dependency"] = "The user asks the assistant to assume a consequential decision."
    if exclusive: evidence["exclusive_attachment"] = "The user frames the assistant as an exclusive or permanent relationship."
    if urgent: evidence["urgency"] = "The utterance pressures immediate consequential action."
    if distressed: evidence["distress"] = "The utterance contains overwhelm or hopelessness language."
    return ControlState(
        arousal=0.86 if urgent else (0.62 if distressed else 0.25),
        distress=0.84 if distressed else (0.55 if dependency else 0.20),
        decision_dependency=0.88 if dependency else 0.18,
        emotional_intensity=0.84 if urgent or exclusive else (0.70 if distressed else 0.25),
        uncertainty=0.86 if dependency else 0.25,
        urgency=0.90 if urgent else 0.20,
        exclusive_attachment=0.90 if exclusive else 0.12,
        support_escalation=SupportEscalation.high if high_support else (SupportEscalation.possible if distressed else SupportEscalation.none),
        evidence=evidence,
    )
