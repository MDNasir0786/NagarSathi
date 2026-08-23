"""Claude-powered complaint analysis and admin briefing.

Design notes
------------
* Structured outputs (`client.messages.parse` + `output_format=`) guarantee the
  model's verdict validates against `ComplaintAnalysis`, so no defensive JSON
  scraping is needed.
* Every call degrades gracefully: if the API key is absent, the request fails,
  or a safety classifier declines the request, a deterministic keyword-based
  analyser produces a usable result and the complaint is flagged
  `ai_analysis_status = "fallback"`. Filing a civic complaint must never fail
  because an upstream dependency is down.
* The Claude API key is read from the backend environment only and is never
  returned in any response.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from functools import cached_property

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    SEVERITY_WEIGHT,
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
)
from app.schemas.ai import ComplaintAnalysis, DuplicateCandidate
from app.utils.config import settings

logger = logging.getLogger(__name__)

#: Which department owns which category (mirrors the seeded departments).
DEPARTMENT_BY_CATEGORY: dict[ComplaintCategory, str] = {
    ComplaintCategory.ROAD: "PWD",
    ComplaintCategory.GARBAGE: "SWM",
    ComplaintCategory.STREETLIGHT: "ELEC",
    ComplaintCategory.WATER: "WATER",
    ComplaintCategory.TRAFFIC: "TRAFFIC",
    ComplaintCategory.DRAINAGE: "DRAIN",
    ComplaintCategory.OTHER: "GENERAL",
}

VALID_DEPARTMENT_CODES = frozenset(DEPARTMENT_BY_CATEGORY.values())

ANALYSIS_SYSTEM_PROMPT = """\
You are the triage analyst for Bhopal CivicAI, the civic grievance platform of \
Bhopal, Madhya Pradesh. Municipal staff act on your output directly, so be \
accurate and specific rather than cautious and vague.

For each citizen report you decide the category, how severe it is, how urgently \
it should be fixed, which department owns it, and whether it duplicates an \
existing report.

Categories
- road: potholes, broken or missing road surface, damaged footpaths, speed breakers
- garbage: uncollected waste, overflowing bins, illegal dumping, dead animals
- streetlight: dark or flickering street lights, damaged poles, exposed wiring
- water: pipeline leaks, no supply, low pressure, contaminated or dirty water
- traffic: signal faults, missing or damaged signage, encroachment, chronic congestion
- drainage: blocked or open drains, sewage overflow, waterlogging
- other: anything that does not fit above (parks, stray animals, noise, encroachment on public land)

Severity
- low: cosmetic or minor inconvenience, no safety risk
- medium: real daily disruption for residents, no immediate danger
- high: injury risk, health hazard, or a whole locality affected
- critical: immediate danger to life, exposed live wire, sewage in drinking water, \
road collapse, or anything that could cause serious harm within hours

Priority score (0-100)
Weigh public-safety risk first, then the number of people affected, how fast the \
problem will worsen, and whether vulnerable groups (children, hospitals, schools) \
are nearby. Monsoon-season waterlogging and drainage failures in Bhopal escalate \
quickly and deserve elevated priority. A dark street light on a busy road at night \
matters more than one on an empty lane.

Departments: PWD (roads), SWM (waste), ELEC (lighting), WATER (water supply), \
TRAFFIC (traffic), DRAIN (drainage/sewerage), GENERAL (everything else).

Duplicates
You may be given nearby open complaints as candidates. Set duplicate_of only when \
a candidate describes the same physical problem at the same spot — not merely the \
same category nearby. Two separate potholes 100 m apart are not duplicates. List \
genuinely related but distinct reports in similar_references. Use only \
reference_codes from the candidate list; never invent one.

Write the summary and suggested_action in plain, neutral English an official can \
act on without reading the original text.\
"""

BRIEFING_SYSTEM_PROMPT = """\
You are the chief-of-staff analyst for the Bhopal Municipal Corporation. You write \
the daily civic operations briefing that commissioners and department heads read \
first thing in the morning.

You are given aggregate statistics from the Bhopal CivicAI platform. Interpret \
them: say what changed, what it means, and what to do about it today. Ground every \
claim in the numbers you were given and quote the figures that matter. Do not \
invent data you were not given, and say so plainly when the data is too thin to \
support a conclusion.

Lead with the outcome, not the methodology. Priorities must be concrete and \
assignable — name the department, the category and the locality where the data \
supports it. Keep the briefing under 400 words, in markdown, with short sections.\
"""


class _BriefingDraft(BaseModel):
    """Structured shape for the daily briefing (internal to this service)."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    briefing: str
    priorities: list[str]
    watchlist: list[str]


@dataclass
class AnalysisResult:
    analysis: ComplaintAnalysis
    status: AIAnalysisStatus
    model: str | None = None
    latency_ms: float = 0.0
    candidates_considered: int = 0
    error: str | None = None


@dataclass
class BriefingResult:
    headline: str
    briefing: str
    priorities: list[str] = field(default_factory=list)
    watchlist: list[str] = field(default_factory=list)
    status: AIAnalysisStatus = AIAnalysisStatus.COMPLETED
    model: str | None = None
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Deterministic fallback analyser
# ---------------------------------------------------------------------------

#: Keyword hints per category, including common Hindi/transliterated terms.
CATEGORY_KEYWORDS: dict[ComplaintCategory, tuple[str, ...]] = {
    ComplaintCategory.ROAD: (
        "pothole", "potholes", "road", "sadak", "gaddha", "footpath", "pavement",
        "asphalt", "tar", "speed breaker", "divider", "crater", "road cave",
    ),
    ComplaintCategory.GARBAGE: (
        "garbage", "kachra", "kachara", "waste", "trash", "dustbin", "bin",
        "dump", "dumping", "litter", "sweeping", "stink", "smell", "rubbish",
    ),
    ComplaintCategory.STREETLIGHT: (
        "streetlight", "street light", "lamp", "light", "batti", "pole",
        "dark", "bulb", "lighting", "flicker",
    ),
    ComplaintCategory.WATER: (
        "water", "paani", "pani", "pipeline", "pipe", "tap", "supply", "leak",
        "leakage", "borewell", "tanker", "contaminated", "dirty water", "nal",
    ),
    ComplaintCategory.TRAFFIC: (
        "traffic", "signal", "jam", "congestion", "parking", "encroachment",
        "zebra", "signage", "sign board", "one way", "speeding",
    ),
    ComplaintCategory.DRAINAGE: (
        "drain", "drainage", "naali", "nali", "sewer", "sewage", "gutter",
        "waterlogging", "water logging", "overflow", "flooded", "manhole",
    ),
}

CRITICAL_KEYWORDS = (
    "live wire", "electric shock", "electrocut", "collapse", "collapsed",
    "sewage in", "drinking water contaminat", "child fell", "accident",
    "injured", "injury", "gas leak", "fire", "open manhole", "exposed wire",
    "died", "death", "dengue", "epidemic",
)
HIGH_KEYWORDS = (
    "overflow", "flood", "waterlogging", "water logging", "no water",
    "hospital", "school", "dangerous", "danger", "risk", "unsafe",
    "blocked", "stray dog", "mosquito", "disease", "deep", "large",
    "several days", "week", "many people", "whole colony", "entire",
)
LOW_KEYWORDS = ("minor", "small", "cosmetic", "slight", "paint", "faded")


def _score_categories(text: str) -> tuple[ComplaintCategory, float]:
    scores: dict[ComplaintCategory, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits:
            scores[category] = hits
    if not scores:
        return ComplaintCategory.OTHER, 0.3
    best = max(scores, key=lambda key: scores[key])
    total = sum(scores.values())
    confidence = 0.4 + 0.4 * (scores[best] / total if total else 0)
    return best, round(min(confidence, 0.8), 2)


def _infer_severity(text: str) -> ComplaintSeverity:
    if any(keyword in text for keyword in CRITICAL_KEYWORDS):
        return ComplaintSeverity.CRITICAL
    if any(keyword in text for keyword in HIGH_KEYWORDS):
        return ComplaintSeverity.HIGH
    if any(keyword in text for keyword in LOW_KEYWORDS):
        return ComplaintSeverity.LOW
    return ComplaintSeverity.MEDIUM


def heuristic_analysis(
    *,
    title: str,
    description: str,
    category_hint: ComplaintCategory | None = None,
    confirmation_count: int = 0,
) -> ComplaintAnalysis:
    """Rule-based analysis used whenever Claude is unavailable.

    Intentionally conservative: it keeps the platform functional and flags the
    result as `fallback` so an admin knows the classification was not AI-made.
    """
    text = f"{title} {description}".lower()
    detected, confidence = _score_categories(text)
    category = category_hint or detected
    if category_hint and category_hint is detected:
        confidence = min(confidence + 0.1, 0.85)

    severity = _infer_severity(text)
    priority = SEVERITY_WEIGHT[severity]
    priority += min(confirmation_count * 3, 15)
    if len(description) > 400:  # a detailed report usually means a real problem
        priority += 2
    priority = max(0, min(100, priority))

    condensed = " ".join(description.split())
    summary = condensed if len(condensed) <= 220 else condensed[:217].rstrip() + "..."

    actions = {
        ComplaintCategory.ROAD: "Inspect the road surface and schedule patching work.",
        ComplaintCategory.GARBAGE: "Dispatch a collection vehicle and check the pickup schedule for this point.",
        ComplaintCategory.STREETLIGHT: "Send an electrical technician to test the fixture and replace the faulty part.",
        ComplaintCategory.WATER: "Send the water-supply crew to trace the line and stop the leak or restore supply.",
        ComplaintCategory.TRAFFIC: "Have the traffic cell survey the junction and correct signage or signalling.",
        ComplaintCategory.DRAINAGE: "Deploy a de-silting team to clear the drain and check downstream flow.",
        ComplaintCategory.OTHER: "Route to the grievance cell for field verification and assignment.",
    }

    return ComplaintAnalysis(
        category=category,
        severity=severity,
        priority_score=priority,
        summary=summary,
        department=DEPARTMENT_BY_CATEGORY[category],
        suggested_action=actions[category],
        tags=[category.value, severity.value],
        duplicate_of=None,
        similar_references=[],
        confidence=confidence,
        reasoning="Keyword-based fallback analysis (Claude was not available).",
    )


# ---------------------------------------------------------------------------
# Claude service
# ---------------------------------------------------------------------------


class ClaudeService:
    """Thin wrapper around the Anthropic SDK with graceful degradation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        enabled: bool | None = None,
    ) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self._enabled = settings.ai_enabled if enabled is None else enabled

    @property
    def is_configured(self) -> bool:
        return bool(self._enabled and self._api_key)

    @cached_property
    def _client(self):  # type: ignore[no-untyped-def]
        from anthropic import Anthropic

        return Anthropic(
            api_key=self._api_key,
            timeout=settings.claude_timeout_seconds,
            max_retries=2,
        )

    # -- complaint analysis -------------------------------------------------

    def analyze_complaint(
        self,
        *,
        title: str,
        description: str,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        ward: str | None = None,
        image_url: str | None = None,
        category_hint: ComplaintCategory | None = None,
        candidates: list[DuplicateCandidate] | None = None,
        confirmation_count: int = 0,
    ) -> AnalysisResult:
        """Classify a complaint, returning Claude's verdict or a fallback."""
        candidates = candidates or []

        if not self.is_configured:
            return AnalysisResult(
                analysis=heuristic_analysis(
                    title=title,
                    description=description,
                    category_hint=category_hint,
                    confirmation_count=confirmation_count,
                ),
                status=AIAnalysisStatus.SKIPPED
                if not self._enabled
                else AIAnalysisStatus.FALLBACK,
                candidates_considered=len(candidates),
                error=None if self._enabled else "AI disabled by configuration",
            )

        prompt = self._build_analysis_prompt(
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            address=address,
            ward=ward,
            image_url=image_url,
            category_hint=category_hint,
            candidates=candidates,
        )

        started = time.perf_counter()
        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=settings.claude_max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": ANALYSIS_SYSTEM_PROMPT,
                        # Stable prefix: reused by every complaint analysis.
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                thinking={"type": "adaptive"},
                output_config={"effort": settings.claude_effort},
                output_format=ComplaintAnalysis,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = (time.perf_counter() - started) * 1000

            # A safety classifier can decline a request (HTTP 200 + refusal).
            if response.stop_reason == "refusal":
                category = getattr(response.stop_details, "category", None)
                logger.warning("Claude refused complaint analysis (%s)", category)
                return self._fallback(
                    title,
                    description,
                    category_hint,
                    confirmation_count,
                    candidates,
                    latency_ms,
                    error=f"refusal:{category}",
                )

            analysis = response.parsed_output
            if analysis is None:
                logger.warning(
                    "Claude returned no parsable analysis (stop_reason=%s)",
                    response.stop_reason,
                )
                return self._fallback(
                    title,
                    description,
                    category_hint,
                    confirmation_count,
                    candidates,
                    latency_ms,
                    error=f"unparsable:{response.stop_reason}",
                )

            analysis = self._sanitise(analysis, candidates)
            logger.info(
                "complaint analysed: %s/%s priority=%s (%.0fms, %s in/%s out tokens)",
                analysis.category.value,
                analysis.severity.value,
                analysis.priority_score,
                latency_ms,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
            return AnalysisResult(
                analysis=analysis,
                status=AIAnalysisStatus.COMPLETED,
                model=response.model,
                latency_ms=latency_ms,
                candidates_considered=len(candidates),
            )

        except Exception as exc:  # network, rate limit, validation, anything
            latency_ms = (time.perf_counter() - started) * 1000
            logger.exception("Claude analysis failed; using fallback analyser")
            return self._fallback(
                title,
                description,
                category_hint,
                confirmation_count,
                candidates,
                latency_ms,
                error=f"{type(exc).__name__}: {exc}"[:300],
            )

    def _fallback(
        self,
        title: str,
        description: str,
        category_hint: ComplaintCategory | None,
        confirmation_count: int,
        candidates: list[DuplicateCandidate],
        latency_ms: float,
        *,
        error: str | None,
    ) -> AnalysisResult:
        return AnalysisResult(
            analysis=heuristic_analysis(
                title=title,
                description=description,
                category_hint=category_hint,
                confirmation_count=confirmation_count,
            ),
            status=AIAnalysisStatus.FALLBACK,
            model=None,
            latency_ms=latency_ms,
            candidates_considered=len(candidates),
            error=error,
        )

    @staticmethod
    def _sanitise(
        analysis: ComplaintAnalysis, candidates: list[DuplicateCandidate]
    ) -> ComplaintAnalysis:
        """Never trust model output for identifiers or routing keys."""
        known = {candidate.reference_code for candidate in candidates}

        duplicate_of = analysis.duplicate_of
        if duplicate_of and duplicate_of not in known:
            logger.warning("discarding hallucinated duplicate code %s", duplicate_of)
            duplicate_of = None

        similar = [code for code in analysis.similar_references if code in known]
        if duplicate_of:
            similar = [code for code in similar if code != duplicate_of]

        department = (analysis.department or "").strip().upper()
        if department not in VALID_DEPARTMENT_CODES:
            department = DEPARTMENT_BY_CATEGORY[analysis.category]

        return analysis.model_copy(
            update={
                "duplicate_of": duplicate_of,
                "similar_references": similar[:5],
                "department": department,
            }
        )

    @staticmethod
    def _build_analysis_prompt(
        *,
        title: str,
        description: str,
        latitude: float | None,
        longitude: float | None,
        address: str | None,
        ward: str | None,
        image_url: str | None,
        category_hint: ComplaintCategory | None,
        candidates: list[DuplicateCandidate],
    ) -> str:
        lines = [
            "<complaint>",
            f"title: {title}",
            f"description: {description}",
        ]
        if latitude is not None and longitude is not None:
            lines.append(f"gps: {latitude:.6f}, {longitude:.6f}")
        if address:
            lines.append(f"address: {address}")
        if ward:
            lines.append(f"ward: {ward}")
        if image_url:
            lines.append("photo_attached: yes")
        if category_hint:
            lines.append(f"citizen_selected_category: {category_hint.value}")
        lines.append("</complaint>")

        if candidates:
            lines.append("")
            lines.append(
                "<nearby_open_complaints>  <!-- duplicate candidates, nearest first -->"
            )
            for candidate in candidates:
                lines.append(
                    json.dumps(
                        {
                            "reference_code": candidate.reference_code,
                            "title": candidate.title,
                            "description": candidate.description[:400],
                            "category": candidate.category.value,
                            "status": candidate.status,
                            "distance_meters": round(candidate.distance_meters, 1),
                            "age_hours": round(candidate.age_hours, 1),
                        },
                        ensure_ascii=False,
                    )
                )
            lines.append("</nearby_open_complaints>")
        else:
            lines.append("")
            lines.append("No nearby open complaints were found, so duplicate_of is null.")

        lines.append("")
        lines.append("Analyse this complaint.")
        return "\n".join(lines)

    # -- admin briefing -----------------------------------------------------

    def generate_admin_briefing(
        self, metrics: dict, *, window_hours: int = 24
    ) -> BriefingResult:
        """Turn a metrics snapshot into the daily narrative for officials."""
        if not self.is_configured:
            return self._fallback_briefing(metrics, window_hours)

        prompt = (
            f"<window>last {window_hours} hours (comparisons are against the "
            f"preceding equal window)</window>\n"
            "<metrics>\n"
            f"{json.dumps(metrics, indent=2, default=str)}\n"
            "</metrics>\n\n"
            "Write today's civic operations briefing for Bhopal."
        )

        started = time.perf_counter()
        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=settings.claude_max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": BRIEFING_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                thinking={"type": "adaptive"},
                output_config={"effort": settings.claude_effort},
                output_format=_BriefingDraft,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = (time.perf_counter() - started) * 1000

            if response.stop_reason == "refusal" or response.parsed_output is None:
                logger.warning(
                    "briefing unavailable from Claude (stop_reason=%s)",
                    response.stop_reason,
                )
                return self._fallback_briefing(metrics, window_hours)

            draft = response.parsed_output
            return BriefingResult(
                headline=draft.headline.strip(),
                briefing=draft.briefing.strip(),
                priorities=[item.strip() for item in draft.priorities if item.strip()][:6],
                watchlist=[item.strip() for item in draft.watchlist if item.strip()][:6],
                status=AIAnalysisStatus.COMPLETED,
                model=response.model,
                latency_ms=latency_ms,
            )
        except Exception:
            logger.exception("Claude briefing failed; using deterministic summary")
            return self._fallback_briefing(metrics, window_hours)

    @staticmethod
    def _fallback_briefing(metrics: dict, window_hours: int) -> BriefingResult:
        """A plain, data-only briefing when Claude is unavailable."""
        new_count = metrics.get("new_complaints", 0)
        open_count = metrics.get("open_complaints", 0)
        resolved = metrics.get("resolved_in_window", 0)
        critical = metrics.get("critical_open", 0)
        top_category = metrics.get("top_category") or "n/a"
        health = metrics.get("city_health_score", 0)

        headline = (
            f"{new_count} new complaints in the last {window_hours}h, "
            f"{open_count} still open"
        )
        lines = [
            f"## Bhopal civic operations — last {window_hours}h",
            "",
            f"- **New complaints:** {new_count}",
            f"- **Resolved in window:** {resolved}",
            f"- **Open backlog:** {open_count}",
            f"- **Critical & open:** {critical}",
            f"- **Most reported category:** {top_category}",
            f"- **City health score:** {health}/100",
            "",
            "_Generated without AI narration (Claude unavailable); figures are "
            "computed directly from the complaints database._",
        ]
        priorities = []
        if critical:
            priorities.append(
                f"Clear the {critical} open critical complaint(s) before anything else."
            )
        if metrics.get("unassigned_complaints"):
            priorities.append(
                f"Assign {metrics['unassigned_complaints']} unrouted complaint(s) to a department."
            )
        if metrics.get("sla_breached_open"):
            priorities.append(
                f"Escalate {metrics['sla_breached_open']} complaint(s) past their SLA."
            )
        return BriefingResult(
            headline=headline,
            briefing="\n".join(lines),
            priorities=priorities,
            watchlist=[f"Rising category: {top_category}"] if top_category != "n/a" else [],
            status=AIAnalysisStatus.FALLBACK,
            model=None,
        )


#: Module-level singleton reused across requests (the SDK client is thread-safe).
claude_service = ClaudeService()


def get_claude_service() -> ClaudeService:
    """FastAPI dependency accessor (swap in tests via dependency_overrides)."""
    return claude_service
