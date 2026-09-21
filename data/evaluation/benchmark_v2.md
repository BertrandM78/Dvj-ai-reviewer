Model: Amazon Nova Pro
Temperature: 0.0
Rules: 31
Proposals: 1
Rule decisions: 31

Accuracy: 93.5%
Violation precision: 75.0%
Violation recall: 75.0%

TP: 3
FP: 1
FN: 1
TN: 26

FN:
RULE_15 — missed missing deliverable format

FP:
RULE_27 — tender rule incorrectly classified as NON_COMPLIANT
when applicability condition was not triggered





Model: Amazon Nova Pro
Prompt: reviewer_prompt_v3
Temperature: 0.0

Dataset:
- 2 realistic proposals
- 62 rule decisions

Results:
Accuracy: 83.9%
Violation precision: 90.9%
Violation recall: 55.6%

TP: 10
FP: 1
FN: 8

Observed failure modes:
- exhaustive checking
- arithmetic
- date reasoning
- cross-section consistency
- semantic relevance
- conditional applicability