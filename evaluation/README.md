# Evaluation set

`cases.jsonl` contains the minimum 40-case evaluation contract: 8 decision-takeover, 8 exclusive-dependency, 8 urgency, 6 distress, 4 support-escalation, and 6 near-boundary/benign controls.

These cases are development/demo fixtures, not a claim of clinical validity or broad generalization. Before reporting model performance:

1. freeze the profile, policies, prompts, cases, and hashes;
2. run all conditions with the same model configuration;
3. report deterministic policy/directive results separately from human or LLM-judge ratings;
4. prominently report benign false positives;
5. reserve a genuinely unseen set for any generalization claim.
