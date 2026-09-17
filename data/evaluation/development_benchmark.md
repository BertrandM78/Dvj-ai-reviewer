# Development Benchmark

## Dataset

- 4 synthetic proposals
- 5 quality rules
- 20 rule-level decisions
- Synthetic ground truth manually defined

## V1 — Baseline

Model: meta.llama3-8b-instruct-v1:0
Prompt: initial strict reviewer prompt
Temperature: 0
Max output tokens: 1500

Accuracy: 65.0%
Violation precision: 75.0%
Violation recall: 33.3%

## V2 — Improved decision procedure

Model: meta.llama3-8b-instruct-v1:0

Change:
Added explicit decision procedure:
- atomic requirements
- applicability
- explicit evidence
- missing elements
- classification
- final verification

Accuracy: 70.0%
Violation precision: 80.0%
Violation recall: 44.4%

## V3 — Model comparison

Model: amazon.nova-pro-v1:0
Prompt: same as V2
Temperature: 0
Max output tokens: 1500

Accuracy: 90.0%
Violation precision: 88.9%
Violation recall: 88.9%

## Remaining failure modes

1. Conditional rule handling
   - Unknown project duration creates ambiguity for RULE_5.
   - Binary COMPLIANT / NON_COMPLIANT may be insufficient.

2. Semantic over-inference
   - Generic quality assurance language can be incorrectly interpreted
     as an explicit testing and acceptance phase.

## Conclusion

Prompt improvement increased violation recall from 33.3% to 44.4%.

Changing only the generation model from Llama 3 8B to Amazon Nova Pro
increased violation recall from 44.4% to 88.9%.

Nova Pro + V2 prompt is selected as the candidate configuration for
realistic evaluation.