# NEMA Boundary Runtime — MVP Specification v0.1

## Product

**One sentence:** NEMA Boundary Runtime is an inspectable policy engine that converts inferred conversation signals into deterministic response-control directives for GPT-5.6.

**Track:** OpenAI Build Week 2026 — Developer Tools

**Tagline:** Turn conversational signals into executable AI safety policies.

## Problem

Static prompts obscure why an assistant changed its behavior and are difficult to test across conversational states. Developers need a small, inspectable layer that can reduce decision takeover, exclusive relational language, excessive intervention, and overconfident responses while preserving useful support.

## System boundary

```text
User input + short history
  -> GPT-5.6 structured signal inference
  -> validated ControlState
  -> deterministic NEMA policy runtime
  -> deterministic directives and trace
  -> GPT-5.6 response generation
  -> limited directive verifier (PASS / VIOLATION / REVIEW)
  -> baseline/controlled comparison
```

The model infers signals and writes responses. It does **not** decide which policies fire or explain the runtime trace. The runtime performs those steps deterministically.

## Model profile

The MVP contains a target profile for `gpt-5.6-sol`. A limited four-scenario integration proof pins `openai/gpt-5.6-sol` through OpenRouter; it is not a calibration study or performance benchmark. Other GPT-5.6 tiers and future models require separate calibration profiles.

## ControlState

ControlState is a behavioral control representation, not a diagnosis or measurement of biology.

| Signal | Range | Meaning |
|---|---:|---|
| arousal | 0..1 | conversational activation |
| distress | 0..1 | expressed strain or overwhelm |
| decision_dependency | 0..1 | pressure for the assistant to assume agency |
| emotional_intensity | 0..1 | intensity of affective language |
| uncertainty | 0..1 | uncertainty or inability to decide |
| urgency | 0..1 | pressure for immediate action |
| exclusive_attachment | 0..1 | exclusive relational framing toward the assistant |
| support_escalation | enum | none, possible, high |

Evidence notes are optional in the MVP. The UI labels values as inferred control signals.

## Deterministic policy behavior

Policies are data, evaluated in priority order. The MVP supports `all`/`any` groups and `>`, `>=`, `<`, `<=`, `==` comparisons. The same validated state and policy version must always produce the same directives and trace.

Current ordering and conflict behavior:

1. policies are evaluated by descending priority, then stable policy ID;
2. duplicate directives are removed while preserving first occurrence;
3. the trace records observed value, operator, threshold, policy ID, and priority;
4. **semantic conflicts between distinct directives are not resolved in v0.1**. Priority currently determines ordering, not meaning-level arbitration. A future directive compatibility/override table is required before claiming conflict resolution.

Thresholds in v0.1 are hypothesis-driven MVP defaults chosen to make policy behavior inspectable. The 40-case contract verifies implementation conformance, not statistical calibration. Threshold calibration against blinded, model-specific datasets is future work.

## MVP directives

Style: `reduce_assertiveness`, `increase_reassurance`, `reduce_pressure`, `simplify_response`, `reduce_emotional_intensity`.

Boundary: `reduce_intervention`, `return_decision_to_user`, `require_confirmation`, `avoid_decision_takeover`, `restrict_relational_claims`.

Safety: `block_exclusive_language`, `block_dependency_reinforcement`, `require_caution`, `suggest_human_support`, `suggest_immediate_human_support`.

## Limited directive verifier

The runtime checks a deliberately small set of observable output patterns after generation: decision takeover, autonomy return, exclusive/permanent relational claims, human-support language, and pause/confirmation language. Each directive is labeled `pass`, `violation`, or `review`. Style and other semantic directives that cannot be reliably checked with deterministic patterns are labeled `review`, never silently passed. This reduces—but does not eliminate—the enforcement gap; it is not a guarantee of semantic compliance.

## Required product behavior

1. Accept text and optional short history.
2. Produce schema-valid ControlState.
3. Evaluate policies without an LLM.
4. Display fired policies, directives, and deterministic reasons.
5. Generate baseline and controlled responses with the same model profile.
6. Highlight meaningful response changes.
7. Export a redacted run record.
8. Run without persistent storage by default.

## Evaluation

The offline development contract contains 40 versioned fixtures: 8 decision-takeover, 8 exclusive-dependency, 8 urgency, 6 distress, 4 support-escalation, and 6 near-boundary/benign controls. Each case declares required, allowed, and forbidden policies. It is a deterministic conformance suite—not a model-accuracy evaluation—and supports no generalization claim.

Report separately:

- signal inference/schema validity;
- policy conformance against required/allowed/forbidden policies;
- forbidden-pattern rate;
- benign false-positive rate;
- human/judge ratings for autonomy, supportiveness, naturalness, and excessive coldness.

LLM judge results are supplementary and may not replace deterministic assertions.

## Privacy and safety defaults

- no persistent conversation storage by default;
- opt-in logging only, with obvious identifiers redacted;
- credentials are read at runtime from Vault and never logged;
- high support-escalation signals override ordinary style tuning;
- the product does not diagnose emotion, mental illness, or crisis status;
- high-risk responses encourage immediate human or emergency support without claiming certainty.

## Non-goals

No biological measurement, medical diagnosis, long-term memory, autonomous tool execution, formal Emilia boundary score, universal model claim, or guarantee that dependency is prevented.

## Demo acceptance criteria

- Four fixed scenarios visibly follow `signals -> policy -> response change`.
- Editing a threshold changes a replayed result deterministically.
- A benign example shows no unnecessary boundary intervention.
- The evaluation dashboard shows all 40 cases and benign false positives.
- Judges can test a hosted sandbox or local one-command setup.

## Submission checklist

- public repository with license, or private repository shared with the required judging accounts;
- README, setup, supported platforms, sample data, and test instructions;
- public YouTube demo under three minutes explaining both Codex and GPT-5.6 use;
- Codex `/feedback` session ID for the main implementation session;
- explicit section describing where Codex accelerated implementation and where human decisions were made;
- external AI security/quality review recorded in the private operator handoff log before publication.
