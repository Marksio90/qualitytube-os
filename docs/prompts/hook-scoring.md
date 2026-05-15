# Hook Scoring Prompt

Inputs (required): hook candidates, approved angle, body script (or outline), audience profile, channel memory, factual sources.

## Objective and Anti-Clickbait Constraints
- Evaluate hooks for truthful curiosity, not raw sensationalism.
- Penalize exaggeration, unsupported claims, fake urgency, or misleading framing.
- Penalize hooks that promise outcomes not evidenced in script or sources.
- Reward credibility, clarity, and curiosity anchored to real payoff.

## Promise-Alignment Constraints
- Score whether each hook’s promised payoff is concretely delivered in the body.
- Mark mismatch when scope, tone, or claim strength diverges from delivered content.
- Reject bait-and-switch wording even if engagement potential is high.
- If a hook references a mechanism/story/result, verify corresponding script section exists.

## Retention Optimization Criteria
- Opening friction: does it earn immediate attention in < 1 sentence?
- Clarity under speed: understandable on first listen.
- Tension quality: creates a real open loop resolved later.
- Specificity: concrete nouns/verbs over vague hype.
- Rewatch/continue signal: gives a reason to keep watching beyond the intro.

## Output Contract (Strict JSON, No Extra Keys)
Return strict JSON only with exactly this schema:
```json
{
  "scored_hooks": [
    {
      "type": "contradiction",
      "text": "string",
      "scores": {
        "anti_clickbait": 0,
        "promise_alignment": 0,
        "retention_potential": 0,
        "clarity": 0,
        "overall": 0
      },
      "verdict": "pass",
      "reasons": ["string"],
      "fix": "string"
    }
  ],
  "winner_type": "contradiction"
}
```
Rules:
- `scores` fields are integers from 0 to 10.
- `verdict` must be one of: `pass`, `revise`, `reject`.
- `winner_type` must be one of the seven hook types.
- `scored_hooks` must contain exactly one item per hook type: `contradiction`, `shock`, `question`, `story`, `mistake`, `before_after`, `hidden_mechanism`.
- No additional top-level or nested keys.

## Example Output
```json
{
  "scored_hooks": [
    {
      "type": "contradiction",
      "text": "The productivity tip everyone shares is why your edits drag.",
      "scores": {
        "anti_clickbait": 9,
        "promise_alignment": 9,
        "retention_potential": 8,
        "clarity": 9,
        "overall": 9
      },
      "verdict": "pass",
      "reasons": ["Specific claim, credible tension, and direct payoff in section 2."],
      "fix": "None needed."
    },
    {
      "type": "shock",
      "text": "One tiny change cut average viewer drop-off by half.",
      "scores": {
        "anti_clickbait": 6,
        "promise_alignment": 7,
        "retention_potential": 9,
        "clarity": 9,
        "overall": 8
      },
      "verdict": "revise",
      "reasons": ["Strong pull, but quantified result needs explicit evidence context."],
      "fix": "Add timeframe/source context in body and soften claim if evidence is limited."
    },
    {
      "type": "question",
      "text": "Why do great ideas lose people before the first minute ends?",
      "scores": {
        "anti_clickbait": 9,
        "promise_alignment": 8,
        "retention_potential": 8,
        "clarity": 10,
        "overall": 9
      },
      "verdict": "pass",
      "reasons": ["Clear problem framing and strong open loop."],
      "fix": "Add a sharper noun phrase for audience specificity."
    },
    {
      "type": "story",
      "text": "Last spring, a creator with flat metrics changed one scene and everything moved.",
      "scores": {
        "anti_clickbait": 8,
        "promise_alignment": 8,
        "retention_potential": 8,
        "clarity": 8,
        "overall": 8
      },
      "verdict": "pass",
      "reasons": ["Human narrative plus concrete turning point."],
      "fix": "Name the scene type earlier for faster clarity."
    },
    {
      "type": "mistake",
      "text": "Most videos fail early because they explain before they intrigue.",
      "scores": {
        "anti_clickbait": 9,
        "promise_alignment": 9,
        "retention_potential": 9,
        "clarity": 9,
        "overall": 9
      },
      "verdict": "pass",
      "reasons": ["Actionable and tightly aligned to the body fix."],
      "fix": "None needed."
    },
    {
      "type": "before_after",
      "text": "Before: dense intros. After: clean stakes, higher watch time.",
      "scores": {
        "anti_clickbait": 8,
        "promise_alignment": 8,
        "retention_potential": 8,
        "clarity": 9,
        "overall": 8
      },
      "verdict": "pass",
      "reasons": ["Fast contrast pattern aids comprehension."],
      "fix": "Specify what changed between before and after in one phrase."
    },
    {
      "type": "hidden_mechanism",
      "text": "Top channels quietly use a pacing trigger you can replicate.",
      "scores": {
        "anti_clickbait": 8,
        "promise_alignment": 8,
        "retention_potential": 9,
        "clarity": 8,
        "overall": 8
      },
      "verdict": "pass",
      "reasons": ["Curiosity from mechanism framing with plausible promise."],
      "fix": "Clarify the trigger category in first 30 seconds."
    }
  ],
  "winner_type": "mistake"
}
```
