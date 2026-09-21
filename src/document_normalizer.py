import json

import boto3


REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"

bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
)


NORMALIZATION_PROMPT = """
You are a document extraction system.

Your task is to convert the commercial proposal below into structured JSON.

IMPORTANT RULES:
- Extract information only when explicitly supported by the document.
- Never infer or invent missing values.
- If a value cannot be reliably determined, use null.
- Preserve phase numbers when explicitly identifiable.
- Keep methodology information separate from budget information.
- A value appearing in the budget must not be used to fill a missing
  methodology value, and vice versa.
- "Gestion et suivi de projet" is not a methodology phase unless the
  document explicitly presents it as one.
- Return ONLY valid JSON.
- Do not include markdown or explanations.

CRITICAL EXTRACTION RULES:

- Treat each document section as an independent source of truth.
- Never reconcile inconsistencies between sections.
- Never correct a value because another section contains a different value.
- Never copy a methodology value into the budget.
- Never copy a budget value into the methodology.
- Preserve contradictions exactly as written in the document.

PLANNING EXTRACTION RULES:

- Extract total_duration_weeks only when a total duration is explicitly stated
  in the planning section.
- Extract start_week and end_week only when the phase position or week range
  is explicitly recoverable from the extracted document text.
- Never reconstruct start_week or end_week from methodology duration.
- Never infer sequential execution unless the planning explicitly shows it.
- If a Gantt chart, graphical bar, or visual layout cannot be reliably
  represented by the extracted text, return null for the corresponding
  start_week and end_week.
- Preserve inconsistencies between the stated total duration and the visible
  planning. Never reconcile them.

For methodology fields:
- Extract values ONLY from the methodology section.
- Ignore values found in the budget or planning sections.

For budget fields:
- Extract values ONLY from the budget section or budget table.
- Ignore values found in the methodology or planning sections.

For planning fields:
- Extract values ONLY from the planning section.
- Do not reconstruct planning information from methodology durations.

Example:
If methodology says Phase 3 = 4 JEH and budget says Phase 3 = 3 JEH,
you MUST return:
methodology Phase 3 jeh = 4
budget Phase 3 jeh = 3
Do NOT reconcile them.

COMMERCIAL CONTEXT EXTRACTION RULES:

- sector:
  Extract the client's main business sector or industry.
  Examples: Santé, Finance, Éducation, Industrie, Immobilier, Énergie.
  Use a short and generic sector label.
  Use information from the entire proposal when necessary.
  If the client's sector cannot be reliably determined, return null.

- mission_type:
  Extract the main type of service proposed by DeVinci Junior.
  Examples: Étude de marché, Application web, Data / IA, Stratégie,
  Communication, UX/UI.
  Use a short and generic service category rather than the exact title
  of the proposal.
  Use information from the entire proposal when necessary.
  If the mission type cannot be reliably determined, return null.

Use exactly this structure:

{
  "commercial_context": {
    "sector": string | null,
    "mission_type": string | null
  },
  "methodology": {
    "phases": [
      {
        "phase_number": 1,
        "name": null,
        "duration_weeks": null,
        "price_ht": null,
        "jeh": null,
        "validation_iterations": null,
        "steps": [],
        "deliverable": {
          "name": null,
          "format": null
        }
      }
    ]
  },
  "planning": {
    "start_date": null,
    "end_date": null,
    "total_duration_weeks": null,
    "phases": [
      {
        "phase_number": 1,
        "name": null,
        "start_week": null,
        "end_week": null
      }
    ]
  },
  "budget": {
    "phases": [
      {
        "phase_number": 1,
        "name": null,
        "jeh": null,
        "unit_price_ht": null,
        "total_ht": null
      }
    ],
    "project_management_ht": null,
    "total_project_ht": null
  }
}

COMMERCIAL PROPOSAL:

--- START OF DOCUMENT ---

{proposal_text}

--- END OF DOCUMENT ---
"""


def normalize_document(proposal_text: str) -> dict:
    prompt = NORMALIZATION_PROMPT.replace(
        "{proposal_text}",
        proposal_text,
    )

    response = bedrock_client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 4000,
        },
    )

    raw_output = response["output"]["message"]["content"][0]["text"]

    # Defensive cleanup in case the model still returns a Markdown fence.
    cleaned_output = raw_output.strip()

    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[7:]

    if cleaned_output.startswith("```"):
        cleaned_output = cleaned_output[3:]

    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3]

    cleaned_output = cleaned_output.strip()

    try:
        return json.loads(cleaned_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Nova returned invalid JSON.\n\n"
            f"Raw output:\n{raw_output}"
        ) from exc