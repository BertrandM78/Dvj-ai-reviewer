from pathlib import Path

PROPOSAL_PATH = Path("data/test_proposals/proposal_001.txt")

proposal = PROPOSAL_PATH.read_text(encoding="utf-8")

#print(proposal)