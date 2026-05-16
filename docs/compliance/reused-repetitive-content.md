# Reused and Repetitive Content Guidance

## Objective

Detect low-originality and mass-produced outputs that may violate quality, policy, or platform integrity requirements.

## Heuristics

Use multiple heuristics; no single signal should be treated as universally determinative.

1. **Near-Duplicate Similarity**
   - High lexical overlap across items with only minor synonym or ordering changes.
   - Repeated intros/outros, call-to-action blocks, or metadata boilerplate.

2. **Template Saturation**
   - Same structure repeated across a batch (headline, bullet cadence, paragraph count, transition phrases).
   - Parameterized substitutions (city/product/name swaps) without substantive content changes.

3. **Semantic Redundancy**
   - Different wording but materially identical claims, examples, or recommendations.
   - Topic coverage that does not introduce net-new value across variants.

4. **Production Pattern Signals**
   - Unnaturally high throughput with minimal editorial delta.
   - Consistent artifact signatures from single-prompt generation (style fingerprinting, phrase loops).

5. **Weak Human Editing Indicators**
   - Edits limited to cosmetic punctuation/spelling.
   - No substantive fact-checking, restructuring, analysis, or contextual adaptation.

## Decision Guidance

- **Compliant**: shared format is present, but each item has substantial unique value, source grounding, and meaningful human editorial changes.
- **Needs Review (Hold)**: signals are mixed; likely reuse but evidence incomplete.
- **Non-Compliant (Block)**: clear near-duplicate or spun mass-production with inadequate differentiation.

## Examples

### Likely Compliant

- A 10-part regional guide series where each entry contains local regulations, unique data, and manually validated references.

### Hold

- A 25-item batch with similar structure and tone, each varying examples slightly but lacking clear new insights.

### Likely Non-Compliant

- 100 pages generated from one template where only brand names and locations change.
- Reposted scripts with line-level paraphrasing but identical argument flow and claims.

## Required Evidence for Clearance

- Similarity analysis summary (lexical + semantic).
- Human edit log indicating substantive contributions.
- Rationale describing unique user value per item.
