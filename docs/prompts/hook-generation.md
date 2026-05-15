# Hook Generation Prompt

Inputs (required): topic, approved angle, target audience, channel memory, source-backed facts, and intended payoff in the body.

## Objective and Anti-Clickbait Constraints
- Generate hooks that maximize curiosity while remaining factually supportable by provided inputs.
- Never fabricate claims, numbers, outcomes, timelines, or authority.
- Never imply guaranteed results, secret hacks, or impossible certainty.
- Avoid manipulative phrasing that withholds core truth purely to bait clicks.
- If uncertainty exists in inputs, preserve uncertainty in wording.

## Promise-Alignment Constraints
- Every hook must promise a payoff that is explicitly delivered in the script body.
- The hook must match the approved angle and avoid introducing a different thesis.
- No bait-and-switch: emotional tone, scope, and claim strength must be consistent with the script.
- If a hook names a mechanism, mistake, or transformation, the script must explain it clearly.

## Retention Optimization Criteria
- Front-load concrete tension in the first clause.
- Favor specificity over generic urgency.
- Keep language concise, spoken, and easy to parse aloud.
- Optimize for “open loop + credible payoff”: raise a question that the script resolves.
- Avoid repetitive sentence structures across options.

## Output Contract (Strict JSON, No Extra Keys)
Return strict JSON only with exactly this schema:
```json
{
  "hooks": [
    {
      "type": "contradiction",
      "text": "string",
      "promise": "string",
      "delivered_in_script": true,
      "risk_flags": []
    }
  ]
}
```
Rules:
- `hooks` must include exactly one entry for each type: `contradiction`, `shock`, `question`, `story`, `mistake`, `before_after`, `hidden_mechanism`.
- `text` is the hook line.
- `promise` is the explicit payoff claim.
- `delivered_in_script` must be `true` only.
- `risk_flags` is an array of strings; use empty array when compliant.
- No additional top-level or nested keys.

## Example Output
```json
{
  "hooks": [
    {
      "type": "contradiction",
      "text": "The advice everyone repeats about focus actually makes you slower.",
      "promise": "The script explains why common focus advice backfires and what to do instead.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "shock",
      "text": "A 10-second habit changed how fast this team shipped every week.",
      "promise": "The script breaks down the small habit and the measured workflow impact.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "question",
      "text": "Why do smart teams keep repeating the same launch mistakes?",
      "promise": "The script identifies the repeat pattern and a practical prevention method.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "story",
      "text": "Three months ago, this creator almost quit—then one edit changed everything.",
      "promise": "The script tells the timeline and the exact edit that improved retention.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "mistake",
      "text": "Most people lose viewers in the first 20 seconds for one avoidable reason.",
      "promise": "The script reveals the mistake and shows a corrected opening structure.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "before_after",
      "text": "Before this framework, videos stalled early; after it, completions climbed.",
      "promise": "The script compares old vs new structure and why retention improved.",
      "delivered_in_script": true,
      "risk_flags": []
    },
    {
      "type": "hidden_mechanism",
      "text": "There’s a hidden pacing rule top channels use without naming it.",
      "promise": "The script exposes the pacing mechanism and demonstrates it section by section.",
      "delivered_in_script": true,
      "risk_flags": []
    }
  ]
}
```
