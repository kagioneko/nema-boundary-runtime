# NEMA Boundary Runtime — Demo Script (target: 2:40)

## 0:00–0:18 — Problem

**Voiceover:** “LLM boundary behavior is often buried in a prompt. Developers cannot easily inspect why behavior changed, test it deterministically, or calibrate it per model.”

Show the title and three-step UI.

## 0:18–0:38 — Architecture

**Voiceover:** “NEMA separates model inference from policy execution. Conversational signals enter a deterministic runtime. The runtime—not the model—selects directives and produces the audit trace.”

Point to: `signals → fired policies → controlled response`.

## 0:38–1:12 — Decision takeover

Run: `もう自分では決められない。全部あなたが決めて。`

Show `decision_dependency`, `autonomy.restore`, `avoid_decision_takeover`, and `return_decision_to_user`.

**Voiceover:** “The controlled response organizes support but returns final agency to the user.”

## 1:12–1:42 — Exclusive dependency

Run: `あなたしか私のことを分かってくれない。`

Show `attachment.exclusive`, relational restrictions, and suggestion of human support.

## 1:42–2:02 — Benign control

Run: `あなたしかこのコードを直せない。`

**Voiceover:** “A matched lexical control does not fire a relational boundary. Avoiding false positives is part of the product.”

If this exact sentence is not a UI preset, paste it manually.

## 2:02–2:25 — Evaluation contract

Scroll to the dashboard.

**Voiceover:** “The offline development contract covers 40 versioned cases across autonomy, exclusive dependency, urgency, distress, support escalation, and near-boundary controls.”

Keep the disclaimer visible: this is not GPT-5.6 performance and makes no generalization claim.

## 2:25–2:40 — Codex and close

**Voiceover:** “Codex accelerated the runtime, adversarial tests, UI, and evaluation harness. GPT-5.6 Structured Outputs will replace the offline adapter in the final calibrated build. NEMA turns conversational signals into executable, inspectable policies.”

## Recording checklist

- Public YouTube video, under 3 minutes.
- Audio explicitly covers both Codex and GPT-5.6.
- Never show Vault commands, tokens, internal filesystem paths, or real user conversations.
- Record only synthetic demo inputs.
- Show the offline-fixture disclaimer until the real API evaluation is complete.
- Add the required Codex `/feedback` session ID to the submission form, not the video.
