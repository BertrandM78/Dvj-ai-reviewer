# Benchmark V3 — Hybrid Reviewer

## Configuration

Model: Amazon Nova Pro  
Prompt: reviewer_prompt_v3  
Temperature: 0.0  

Architecture:
- Amazon Nova Pro for semantic rule evaluation
- Deterministic Python validation for objective rules
- Deterministic results override LLM decisions before final evaluation

Deterministic rules:
- RULE_10 — minimum number of explicit methodology steps
- RULE_13 — validation iteration frequency
- RULE_19 — project start date must not fall on a weekend
- RULE_20 — announced duration vs schedule consistency
- RULE_23 — methodology vs budget JEH consistency
- RULE_25 — project management fee ratio

Reference rules:
- 31 mandatory rules loaded exhaustively
- Mandatory rules are not dependent on semantic top-k retrieval

## Dataset

- 2 realistic synthetic proposals
- 31 rules per proposal
- 62 rule decisions

Proposal 001:
- Mostly compliant proposal
- Contains controlled quality issues

Proposal 002:
- Stress-test proposal
- Contains multiple structural, semantic, financial and consistency issues

## Results

Accuracy: 87.1%  
Violation precision: 91.7%  
Violation recall: 61.1%

TP: 11  
FP: 1  
FN: 7

Correct classifications: 54/62

## Deterministic validation results

| Rule | Check | Proposal 001 | Proposal 002 |
|---|---|---|---|
| RULE_10 | Methodology step count | COMPLIANT | NON_COMPLIANT |
| RULE_13 | Validation frequency | COMPLIANT | NON_COMPLIANT |
| RULE_19 | Weekend start date | COMPLIANT | NON_COMPLIANT |
| RULE_20 | Schedule duration consistency | COMPLIANT | NON_COMPLIANT |
| RULE_23 | Methodology/budget JEH consistency | COMPLIANT | NON_COMPLIANT |
| RULE_25 | Project management fee ratio | COMPLIANT | NON_COMPLIANT |

All deterministic checks matched the benchmark ground truth.

## Remaining errors

### Proposal 001

False negatives:
- RULE_02 — proposal validity/date consistency
- RULE_15 — missing deliverable format

### Proposal 002

False negatives:
- RULE_02 — proposal validity/date consistency
- RULE_09 — relevance of previous references
- RULE_27 — tender applicability / required fees
- RULE_28 — team relevance
- RULE_30 — required closing section

False positive:
- RULE_21 — dependency / parallel-phase consistency

## Observed remaining failure modes

The remaining errors are concentrated around:

- semantic relevance
- conditional applicability
- exhaustive detection of missing information
- interpretation of cross-phase dependencies
- detection of required sections/content

These checks remain handled primarily by the LLM.

## Architecture evolution

### Initial approach

Mandatory quality rules were stored in the Bedrock Knowledge Base and
retrieved using semantic top-k retrieval before generation.

Testing showed that only 24 of the 31 mandatory rules were retrieved.

Documentary recall:

24 / 31 = 77.4%

This demonstrated that semantic retrieval was not appropriate for an
exhaustive mandatory policy.

### Revised approach

Mandatory rules are now loaded directly and exhaustively.

The system separates:

1. exhaustive policy evaluation;
2. deterministic validation for objective rules;
3. LLM reasoning for semantic rules.

The Knowledge Base is therefore no longer required to retrieve mandatory
quality rules and can later be used for contextual retrieval, such as
finding similar historical missions.

## Conclusion

V3 validates the hybrid architecture.

Compared with the LLM-only reviewer, deterministic validation removes
LLM uncertainty from objective checks involving counting, arithmetic,
dates and explicit cross-section consistency.

Final V3 benchmark:

- 87.1% rule accuracy
- 91.7% violation precision
- 61.1% violation recall
- 6 deterministic rules validated against the ground truth

The objective of the next iteration is not to optimize this synthetic
benchmark further.

Next priority:
real PDF proposal ingestion, followed by evaluation on a larger and more
realistic dataset.