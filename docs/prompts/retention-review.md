# Retention Review Prompt

Inputs (required): selected hook, full script or outline, chapter timing plan, target audience, channel memory, evidence links.

## Objective and Anti-Clickbait Constraints
- Diagnose retention risk while preserving truthful framing.
- Do not recommend sensational edits that overpromise or distort evidence.
- Flag any line that creates misleading expectations versus delivered content.
- Prefer trust-preserving revisions over short-term click optimization.

## Promise-Alignment Constraints
- Validate that hook promises are fulfilled in the first meaningful payoff window.
- Ensure each major open loop is resolved clearly and on time.
- Detect bait-and-switch transitions, omitted explanations, and unsupported claims.
- Require consistency between title/hook/intro framing and final conclusion.

## Retention Optimization Criteria
- First 30 seconds: immediate stakes, clear context, no throat-clearing.
- Minute-by-minute tension map: each segment must add novelty or consequence.
- Cognitive load: reduce jargon bursts and long setup blocks.
- Payoff cadence: deliver mini-resolutions before major reveal.
- Momentum hygiene: cut duplication, flattening tangents, and weak transitions.

## Output Contract (Strict JSON, No Extra Keys)
Return strict JSON only with exactly this schema:
```json
{
  "retention_review": {
    "overall_risk": "low",
    "promise_alignment": {
      "status": "aligned",
      "notes": ["string"]
    },
    "timeline": [
      {
        "segment": "00:00-00:30",
        "risk_level": "low",
        "issue": "string",
        "recommendation": "string"
      }
    ],
    "hook_type_checks": {
      "contradiction": "pass",
      "shock": "pass",
      "question": "pass",
      "story": "pass",
      "mistake": "pass",
      "before_after": "pass",
      "hidden_mechanism": "pass"
    },
    "top_fixes": ["string"]
  }
}
```
Rules:
- `overall_risk` must be one of: `low`, `medium`, `high`.
- `status` must be one of: `aligned`, `partial`, `misaligned`.
- `risk_level` must be one of: `low`, `medium`, `high`.
- `hook_type_checks` values must be one of: `pass`, `revise`, `fail`.
- Include all seven hook types in `hook_type_checks`.
- No additional top-level or nested keys.

## Example Output
```json
{
  "retention_review": {
    "overall_risk": "medium",
    "promise_alignment": {
      "status": "partial",
      "notes": [
        "Primary hook promise is delivered, but the supporting mechanism appears later than expected.",
        "One quantified claim in the intro needs clearer sourcing when first mentioned."
      ]
    },
    "timeline": [
      {
        "segment": "00:00-00:30",
        "risk_level": "medium",
        "issue": "Stake is clear, but setup adds two abstract sentences before concrete example.",
        "recommendation": "Move the concrete example into sentence two and cut one abstract line."
      },
      {
        "segment": "00:30-02:00",
        "risk_level": "low",
        "issue": "Strong narrative progression with visible consequence.",
        "recommendation": "Keep pacing; add a micro-tease before section transition."
      },
      {
        "segment": "02:00-04:00",
        "risk_level": "medium",
        "issue": "Jargon density spikes and slows comprehension.",
        "recommendation": "Replace specialized terms with one plain-language analogy."
      }
    ],
    "hook_type_checks": {
      "contradiction": "pass",
      "shock": "revise",
      "question": "pass",
      "story": "pass",
      "mistake": "pass",
      "before_after": "pass",
      "hidden_mechanism": "revise"
    },
    "top_fixes": [
      "Deliver mechanism explanation within first 90 seconds.",
      "Attach source context immediately after quantified claim.",
      "Trim repetitive bridge sentence between sections two and three."
    ]
  }
}
```
