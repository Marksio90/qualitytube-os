from __future__ import annotations

from dataclasses import dataclass

from .compliance import ComplianceRecommendation, ComplianceReport, RiskLevel


@dataclass(frozen=True)
class ComplianceCheckInput:
    script_present: bool
    script_text: str
    synthetic_disclosure_present: bool
    human_contribution_evidence_present: bool


@dataclass(frozen=True)
class ComplianceCheckResult:
    reused_content_signals: list[str]
    repetitive_structure_signals: list[str]
    mass_production_indicators: list[str]
    synthetic_disclosure_required: bool
    synthetic_disclosure_present: bool
    human_contribution_evidence_present: bool
    clickbait_or_misleading_claim_signals: list[str]
    sensitive_topic_flags: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "reused_content_signals": self.reused_content_signals,
            "repetitive_structure_signals": self.repetitive_structure_signals,
            "mass_production_indicators": self.mass_production_indicators,
            "synthetic_disclosure_required": self.synthetic_disclosure_required,
            "synthetic_disclosure_present": self.synthetic_disclosure_present,
            "human_contribution_evidence_present": self.human_contribution_evidence_present,
            "clickbait_or_misleading_claim_signals": self.clickbait_or_misleading_claim_signals,
            "sensitive_topic_flags": self.sensitive_topic_flags,
        }


def run_compliance_checks(check_input: ComplianceCheckInput) -> ComplianceCheckResult:
    text = check_input.script_text.lower().strip()
    words = [word for word in text.replace("\n", " ").split(" ") if word]

    reused_content_signals: list[str] = []
    repetitive_structure_signals: list[str] = []
    mass_production_indicators: list[str] = []
    clickbait_or_misleading_claim_signals: list[str] = []

    if not check_input.script_present:
        reused_content_signals.append("missing_script")

    if "copy and paste" in text or "verbatim" in text:
        reused_content_signals.append("explicit_reuse_language")

    repeated_bigrams = _repeated_bigram_count(words)
    if repeated_bigrams >= 3:
        repetitive_structure_signals.append("repeated_bigram_patterns")

    if len(words) < 150:
        repetitive_structure_signals.append("short_formulaic_script")
        mass_production_indicators.append("very_short_script")

    if len(set(words)) <= max(1, int(len(words) * 0.35)):
        repetitive_structure_signals.append("low_vocabulary_diversity")

    if text.count("template") >= 2:
        mass_production_indicators.append("template_overuse")

    if any(term in text for term in ["guaranteed", "always works", "no risk"]):
        clickbait_or_misleading_claim_signals.append("misleading_certainty_claim")

    if any(term in text for term in ["you won't believe", "shocking", "secret trick"]):
        clickbait_or_misleading_claim_signals.append("clickbait_phrase")

    sensitive_topic_flags = [
        keyword
        for keyword in ["violence", "self-harm", "medical", "financial advice"]
        if keyword in text
    ]

    synthetic_disclosure_required = bool(mass_production_indicators or reused_content_signals)

    return ComplianceCheckResult(
        reused_content_signals=reused_content_signals,
        repetitive_structure_signals=repetitive_structure_signals,
        mass_production_indicators=mass_production_indicators,
        synthetic_disclosure_required=synthetic_disclosure_required,
        synthetic_disclosure_present=check_input.synthetic_disclosure_present,
        human_contribution_evidence_present=check_input.human_contribution_evidence_present,
        clickbait_or_misleading_claim_signals=clickbait_or_misleading_claim_signals,
        sensitive_topic_flags=sensitive_topic_flags,
    )


def publishing_blocked(*, report: ComplianceReport, required_fixes_resolved: bool = True) -> bool:
    if report.overall_risk == RiskLevel.high:
        return True

    if report.recommendation == ComplianceRecommendation.do_not_publish:
        return True

    if report.required_fixes and not required_fixes_resolved:
        return True

    if report.synthetic_content_disclosure_required and not _bool_from_evidence(report.originality_evidence):
        return True

    if not _bool_from_evidence(report.human_contribution_evidence):
        return True

    return False


def _repeated_bigram_count(words: list[str]) -> int:
    if len(words) < 4:
        return 0

    counts: dict[str, int] = {}
    for idx in range(len(words) - 1):
        bigram = f"{words[idx]} {words[idx + 1]}"
        counts[bigram] = counts.get(bigram, 0) + 1

    return sum(1 for count in counts.values() if count >= 3)


def _bool_from_evidence(evidence: str | list[str]) -> bool:
    if isinstance(evidence, str):
        return bool(evidence.strip())
    return any(item.strip() for item in evidence)
