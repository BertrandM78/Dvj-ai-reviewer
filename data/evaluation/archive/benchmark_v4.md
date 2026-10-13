# DVJ AI Proposal Reviewer — V0 Benchmark

## Objective

Evaluate the ability of the DVJ AI Proposal Reviewer to classify proposal
quality requirements against a predefined set of 31 business rules.

The benchmark evaluates rule-level classification into three statuses:

- `COMPLIANT`
- `NON_COMPLIANT`
- `NOT_APPLICABLE`

The objective is not to estimate production-level performance, but to provide
a reproducible benchmark for the current V0 system.

---

## Dataset

The benchmark contains three proposals:

| Proposal | Type | Rule decisions |
|---|---|---:|
| proposal_001 | Synthetic | 31 |
| proposal_002 | Synthetic | 31 |
| DE-0426-1002-1017-1075 | Real proposal | 31 |
| **Total** | | **93** |

The two synthetic proposals were designed to contain known compliant and
non-compliant cases.

The real proposal provides a first test on a realistic document structure
and PDF extraction pipeline.

Because the benchmark is small and some documents were used during system
development, these results must not be interpreted as production accuracy.

---

## Architecture evaluated

The V0 system uses a hybrid architecture:

1. PDF/TXT document ingestion
2. PDF text extraction with PyMuPDF when applicable
3. LLM-based document normalization with Amazon Nova Pro
4. Structured JSON representation of methodology, planning and budget
5. Deterministic validation for objective business rules
6. Semantic LLM review for remaining rules
7. Merge into a final 31-rule review report

Six rules are evaluated deterministically:

- RULE_10 — Minimum methodology steps
- RULE_13 — Validation iteration frequency
- RULE_19 — Project start date
- RULE_20 — Planning duration consistency
- RULE_23 — JEH consistency
- RULE_25 — Project management fee ratio

The remaining 25 rules are evaluated semantically using Amazon Nova Pro.

---

## Global results

| Metric | Result |
|---|---:|
| Correct classifications | 81 / 93 |
| Rule accuracy | **87.1%** |
| Violation precision | **90.0%** |
| Violation recall | **64.3%** |
| True positives | 18 |
| False positives | 2 |
| False negatives | 10 |

### Deterministic rule engine

The six deterministic rules were evaluated across all three benchmark
documents.

| Rule | proposal_001 | proposal_002 | Real PDF |
|---|---|---|---|
| RULE_10 | ✓ | ✓ | ✓ |
| RULE_13 | ✓ | ✓ | ✓ |
| RULE_19 | ✓ | ✓ | ✓ |
| RULE_20 | ✓ | ✓ | ✓ |
| RULE_23 | ✓ | ✓ | ✓ |
| RULE_25 | ✓ | ✓ | ✓ |

**Deterministic benchmark result: 18 / 18 correct classifications.**

---

## Error analysis

The final system produced 12 classification errors across 93 decisions.

Errors occurred on:

- RULE_02: 1
- RULE_06: 1
- RULE_07: 1
- RULE_09: 1
- RULE_11: 1
- RULE_15: 2
- RULE_18: 1
- RULE_21: 1
- RULE_27: 1
- RULE_28: 2

The system produced substantially more false negatives than false positives:

- False positives: 2
- False negatives: 10

This indicates that the current V0 is relatively conservative when reporting
violations: detected violations have high precision, but some actual
violations remain undetected.

RULE_15 and RULE_28 are the only rules with errors on more than one benchmark
document.

---

## Key engineering finding

An initial retrieval-based approach was not appropriate for mandatory,
exhaustive business rules because semantic retrieval did not reliably return
all 31 rules.

The V0 architecture therefore separates:

- exhaustive policy rules, loaded directly;
- semantic LLM reasoning;
- deterministic validation for objectively verifiable requirements.

For structured cross-section checks, the system uses an LLM normalization
layer followed by deterministic Python validation.

This creates the following pipeline:

PDF/TXT
→ text extraction
→ LLM document normalization
→ structured JSON
→ deterministic + semantic validation
→ 31-rule report

---

## Limitations

This benchmark has several important limitations:

1. Only three proposals are evaluated.
2. Two of the three proposals are synthetic.
3. Benchmark documents were used during development and debugging.
4. The real proposal represents only one document layout.
5. The benchmark does not yet measure end-user review time or business impact.
6. LLM normalization remains probabilistic even when temperature is set to 0.
7. The 87.1% accuracy must therefore be interpreted as benchmark accuracy,
   not production accuracy.

---

## Next evaluation

The next evaluation phase should use previously unseen proposals and human
reviewers.

The main metrics should be:

- rule-level accuracy on unseen proposals;
- violation precision and recall;
- first-review time without the tool;
- first-review time with the tool;
- useful issues detected;
- false alerts;
- reviewer feedback.

This will allow the project to move from a technical benchmark to a measure
of real operational value.