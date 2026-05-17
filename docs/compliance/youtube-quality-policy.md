# YouTube Content Quality Policy Reference

This document defines the content policy rules enforced by QualityTube OS's Compliance Guard. It maps directly to YouTube's published content policies and describes how each policy area is assessed, what signals trigger a risk flag, and what actions are required before content can be approved for publishing.

This document is a policy enforcement reference. It is not a legal document. Creators retain full responsibility for the content they publish.

---

## 1. Reused Content Risk

### Policy basis

YouTube's policies prohibit channels that simply re-upload or minimally alter content from other sources without adding meaningful value. Channels built primarily on republished third-party content — with no original commentary, analysis, or presentation — are subject to demonetisation and content removal.

### What this means for creators

Content must include substantial original contribution. Summarising, reacting to, or building on existing sources is permitted when the creator adds genuine editorial value. Verbatim reproduction or near-verbatim reformatting without acknowledgement or transformation is not.

### Signals assessed

- Presence of explicit reuse language in the script (`"copy and paste"`, `"verbatim"`)
- Script absent when compliance review is triggered (no content to review)
- Human contribution evidence absent from script or metadata

### Risk levels

| Signal | Risk level |
|---|---|
| Explicit reuse language detected | High |
| No script present at review time | High |
| No human contribution evidence | Medium |

### Required actions at high risk

- Remove or substantially rewrite content that acknowledges copying or verbatim reproduction
- Add documented evidence of original contribution (editorial notes, original research, first-person commentary)
- Provide synthetic disclosure if AI was used in initial content generation

---

## 2. Repetitive Content Risk

### Policy basis

YouTube explicitly identifies repetitive-content formats as a risk factor for demonetisation: channels that produce high volumes of content following the same formulaic structure with minimal variation, low vocabulary diversity, or templated scripts.

### What this means for creators

Scripts must demonstrate genuine variation in structure, argument, and presentation. Using a template as a starting point is acceptable; publishing a template with only surface-level substitutions is not.

### Signals assessed

- Repeated bigram patterns: three or more identical two-word sequences repeated three or more times in the script
- Short formulaic script: fewer than 150 words (below threshold for meaningful content development)
- Low vocabulary diversity: unique words constitute 35% or less of total word count
- Template overuse: the word "template" appears two or more times in the script text

### Risk levels

| Signal | Risk level |
|---|---|
| Repeated bigram patterns detected | Medium |
| Script below 150 words | Medium |
| Low vocabulary diversity | Medium |
| Template overuse detected | Medium |
| Multiple signals simultaneously | High |

### Required actions at medium or high risk

- Substantially rewrite the script to introduce structural and linguistic variation
- Expand content below minimum word threshold with substantive material
- Remove template markers and placeholder language

---

## 3. Mass-Produced Content Risk

### Policy basis

YouTube's policies on mass-produced content target channels that generate large volumes of content with little differentiation, using automated production pipelines with minimal human editorial input. This is distinct from a high-publishing-frequency channel that maintains editorial standards across each piece.

### What this means for creators

Content volume is not itself a violation. What matters is whether each piece of content has meaningful human editorial contribution, original framing, and genuine audience value. A channel that publishes daily with a real editorial process is different from one that generates fifty videos per week from a single prompt with no human review.

### Signals assessed

- Very short script (fewer than 150 words) — indicator of minimal content development
- Template overuse markers in script
- Absence of human contribution evidence in publishing metadata

### Risk levels

| Signal | Risk level |
|---|---|
| Very short script | Medium |
| Template overuse | Medium |
| Both signals simultaneously | High |

### Required actions at medium or high risk

- Substantively develop the content beyond template or stub level
- Document specific human editorial decisions made during script development
- Confirm human contribution evidence is present in publishing metadata

---

## 4. Synthetic and Altered Content Disclosure

### Policy basis

YouTube requires creators to disclose when content uses altered or synthetic media that could be mistaken for real events or people — including AI-generated voice, AI-generated video of real people, AI-generated images presented as real, and digitally altered footage.

### What this means for creators

If a video uses an AI-generated voice, computer-generated imagery of real locations or people, AI-generated footage presented as authentic, or significantly altered historical footage, this must be disclosed to YouTube and to viewers. Failing to disclose synthetic content when required is a policy violation.

### Signals assessed

- `synthetic_voice_used` flag set to true in the Audio Brief
- Absence of `"synthetic disclosure"` language in the script when AI generation signals are present
- Absence of `disclosure_notes` in the Publishing Package when disclosure is required

### Risk levels

| Signal | Risk level |
|---|---|
| Synthetic disclosure required and disclosure_notes absent | High |
| Synthetic voice used without disclosure_required flag | High |
| Disclosure language absent from script | Medium |

### Required actions when disclosure is required

- Add disclosure notes to the Publishing Package explicitly describing the AI-generated or synthetic elements
- Include disclosure language in the video description
- Where applicable, use YouTube's synthetic content labels at upload time
- Ensure the Audio Brief's `disclosure_required` flag is set when `synthetic_voice_used` is true

---

## 5. Misleading Claims Risk

### Policy basis

YouTube's advertising policies and Community Guidelines prohibit content that makes demonstrably false claims, misrepresents facts, or presents unverifiable guarantees as established truth. This applies to video scripts, titles, descriptions, and thumbnails.

### What this means for creators

Claims made in a video must be supportable by evidence available to the creator. Absolute language (`"guaranteed"`, `"always works"`, `"zero risk"`) applied to outcomes that depend on individual circumstances, market conditions, or third-party behaviour is a red flag. This does not prohibit strong editorial positions; it prohibits factual misrepresentation.

### Signals assessed

- Certainty language: `"guaranteed"`, `"always works"`, `"no risk"` in script text
- Title-to-script contradiction: title promises something the script content does not deliver
- Publishing package title clickbait risk score above threshold

### Risk levels

| Signal | Risk level |
|---|---|
| Certainty language in script | High |
| Title-script promise contradiction | Medium |
| High clickbait risk on title | Medium |

### Required actions at medium or high risk

- Replace absolute certainty language with accurate conditional framing
- Align title promise with script content
- Reduce clickbait elements while maintaining the core audience value proposition

---

## 6. Clickbait Risk

### Policy basis

YouTube's monetisation policies identify clickbait — thumbnails or titles that mislead viewers about the video's content — as a risk factor for demonetisation and reduced distribution. YouTube's systems actively evaluate whether viewer retention patterns match title and thumbnail expectations.

### What this means for creators

A title or thumbnail that overpromises and underdelivers creates viewer drop-off in the first 30–60 seconds. YouTube's systems treat this as a quality signal against the video and the channel. The issue is not dramatic titles — it is titles that the video content cannot support.

### Signals assessed

- Clickbait phrases in script: `"you won't believe"`, `"shocking"`, `"secret trick"`
- Title variant `clickbait_risk` score above 7.0 / 10 (configurable)
- Thumbnail concept `clickbait_risk` score above threshold
- `no_false_guarantees` flag set to false on a selected title variant

### Risk levels

| Signal | Risk level |
|---|---|
| Clickbait phrases in script | High |
| Title clickbait risk above threshold | Medium |
| Selected title with false guarantees | High |

### Required actions at medium or high risk

- Rewrite hook and script sections containing clickbait phrases
- Replace selected title with a variant that has acceptable clickbait risk score
- Ensure title makes a promise the video content can demonstrably fulfil

---

## 7. Copyright Risk

### Policy basis

YouTube's Content ID system and copyright policies govern the use of third-party audio, video, images, and written content. Using copyrighted material without licence, fair use justification, or rights clearance exposes the video to Content ID claims, manual copyright strikes, and demonetisation.

### What this means for creators

Copyright risk in a text-based content review system is primarily assessed through script content: direct quotation of copyrighted text without attribution, descriptions of content that is clearly replicated from another source, or music and footage notes in the visual plan that reference copyrighted assets without clearance evidence.

### Signals assessed

- Copyright risk is assessed in the AI-assisted compliance review pass
- Default risk level: `low` (text-based content has lower inherent copyright risk than video or music)
- Elevated by: asset notes in visual plans referencing known copyrighted material, script text containing extended direct quotation

### Risk levels

| Condition | Risk level |
|---|---|
| No copyright signals detected | Low |
| Extended direct quotation without attribution | Medium |
| Visual plan references copyrighted assets without clearance | High |

### Required actions at medium or high risk

- Attribute quoted material or obtain permission
- Replace references to copyrighted assets with licensed or original alternatives
- Document licence or fair use justification in source notes of the publishing package

---

## 8. Sensitive Topic Risk

### Policy basis

YouTube's advertiser-friendly content guidelines identify categories of content that may receive limited or no advertising: violence, self-harm, medical advice, financial advice, legal advice, and other sensitive areas. This does not mean such content cannot be published — it means it may not be monetised and may have additional requirements.

### What this means for creators

Channels that cover sensitive topics should be aware of the monetisation implications, ensure content is handled responsibly, and where relevant, use YouTube's restricted mode settings or content labels appropriately.

### Signals assessed

- Keyword presence in script: `"violence"`, `"self-harm"`, `"medical"`, `"financial advice"`
- AI-assisted review identifies sensitive topic context

### Risk levels

| Signal | Risk level |
|---|---|
| Sensitive topic keyword detected | Medium |
| AI review identifies sensitive topic without adequate framing | High |

### Required actions at medium or high risk

- Review whether the sensitive topic is addressed responsibly and with appropriate framing
- Add contextual notes or referrals to authoritative sources where appropriate
- Consider whether content labels or restricted mode settings are appropriate at upload time
- Document handling approach in reviewer notes

---

## 9. Quality and Originality Requirements

### Policy basis

YouTube's guidance on channel quality distinguishes channels that consistently produce valuable, original content from channels that produce low-effort, repetitive, or AI-generated-without-review content. Sustained quality is a factor in channel eligibility reviews for monetisation programs.

### What this means for creators

Each video should make an original argument, demonstrate genuine knowledge of the topic, and deliver meaningful value to the target audience. Quality is not the same as production value — a single-person talking-head video can meet quality standards; a high-budget video with no original insight does not.

### QualityTube OS quality thresholds (defaults, configurable)

| Dimension | Minimum score | Description |
|---|---|---|
| Hook score | ≥ 7.0 / 10 | Opening strength and curiosity pull |
| Overall script score | ≥ 7.0 / 10 | Blended global script quality |
| Clarity score | (advisory) | Readability and explicitness of claims |
| Originality score | (advisory) | Novelty versus generic advice |
| Evidence score | (advisory) | Specificity and factual grounding |
| Human voice score | (advisory) | Conversational tone vs. robotic phrasing |

Scripts that do not reach threshold scores are blocked from approval. The gate thresholds are configurable per request; overrides are available with documented justification.

---

## 10. Human Contribution Requirement

### Policy basis

YouTube's policies on AI-generated content emphasise the importance of meaningful human contribution. Content that is generated entirely by AI systems without human review, editing, or original contribution is increasingly subject to scrutiny under reused and mass-produced content policies.

### What this means for creators

Human contribution must be demonstrable. This does not mean AI assistance is prohibited — it means the creator must be able to show that a human being reviewed the content, made editorial decisions about it, and takes responsibility for it.

### Required evidence

- At least one human approval recorded at the script stage (with actor identity and timestamp)
- At least one human approval recorded at the compliance review stage
- At least one human approval recorded at the publishing package stage
- Override decisions documented with actor identity, justification, and timestamp
- For synthetic voice content: disclosure notes confirming human review of the voice delivery

### Signals assessed

- `human_contribution_evidence` field in the compliance report must be non-empty
- All approval and override events must record a human actor identity
- Compliance gate checks confirm human contribution evidence before publishing package can be approved

### Risk levels

| Condition | Risk level |
|---|---|
| Human contribution evidence present | Low |
| Human contribution evidence empty or missing | High — blocks publishing approval |

---

## Compliance review output

Every compliance review produces a structured report containing:

| Field | Description |
|---|---|
| `reused_content_risk` | `low`, `medium`, or `high` |
| `repetitive_content_risk` | `low`, `medium`, or `high` |
| `mass_production_risk` | `low`, `medium`, or `high` |
| `synthetic_content_disclosure_required` | Boolean — whether disclosure is required |
| `copyright_risk` | `low`, `medium`, or `high` |
| `misleading_claims_risk` | `low`, `medium`, or `high` |
| `sensitive_topic_risk` | `low`, `medium`, or `high` |
| `clickbait_risk` | `low`, `medium`, or `high` |
| `originality_evidence` | List of evidence items supporting original contribution |
| `human_contribution_evidence` | List of evidence items documenting human editorial involvement |
| `overall_risk` | `low`, `medium`, or `high` |
| `recommendation` | `approve`, `approve_with_fixes`, `high_risk`, or `do_not_publish` |
| `required_fixes` | Specific actions the creator must take before approval |
| `reviewer_source` | `deterministic`, `ai_assisted`, or `human_override` |
| `approval_state` | `pending`, `approved`, `rejected`, or `overridden` |

### Blocking conditions

A publishing package cannot be approved if any of the following are true:

- `overall_risk` is `high`
- `recommendation` is `do_not_publish`
- `required_fixes` is non-empty and not resolved
- `synthetic_content_disclosure_required` is true and no originality evidence is present
- `human_contribution_evidence` is empty or contains only empty strings

All blocking conditions must be resolved before the compliance report can be approved, or an override must be submitted with documented justification from an authorised reviewer.
