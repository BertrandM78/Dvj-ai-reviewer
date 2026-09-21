from src.reviewer import review_file


result = review_file(
    "data/test_proposals/proposal_001.txt"
)

print("TOP LEVEL KEYS:", result.keys())

print("\nCOMMERCIAL CONTEXT")
print(result["commercial_context"])

print("\nHISTORICAL SUMMARY")
print(result["historical_summary"])

print("\nREVIEW")
print(
    len(result["review"].get("results", [])),
    "rules returned"
)