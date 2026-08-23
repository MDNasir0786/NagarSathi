"""Claude service tests.

These run without an ANTHROPIC_API_KEY. They cover the three things that can
realistically break in production:

1. the structured-output schema we send is actually valid for the API,
2. the request is built with the parameters we intend, and
3. every failure mode (refusal, unparsable reply, transport error, missing key)
   degrades to the deterministic analyser instead of raising.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from anthropic.lib._parse._transform import transform_schema
from pydantic import TypeAdapter

from app.models.enums import (
    AIAnalysisStatus,
    ComplaintCategory,
    ComplaintSeverity,
)
from app.schemas.ai import ComplaintAnalysis, DuplicateCandidate
from app.services.claude_service import (
    ClaudeService,
    _BriefingDraft,
    heuristic_analysis,
)

# ---------------------------------------------------------------------------
# Structured-output contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", [ComplaintAnalysis, _BriefingDraft])
def test_output_schema_survives_sdk_transform(model):
    """The SDK must be able to turn our model into a supported JSON schema.

    An unsupported construct (numeric bounds, minLength, recursion) would only
    surface as a 400 at runtime, so assert it here instead.
    """
    schema = transform_schema(TypeAdapter(model).json_schema())
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"], "at least one field must be required"


def test_analysis_schema_has_no_unsupported_keywords():
    schema = transform_schema(TypeAdapter(ComplaintAnalysis).json_schema())
    unsupported = {"minimum", "maximum", "minLength", "maxLength", "multipleOf", "minItems"}
    stack = [schema]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            assert not (unsupported & node.keys()), f"unsupported keyword in {node}"
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


def test_enum_values_reach_the_schema():
    schema = transform_schema(TypeAdapter(ComplaintAnalysis).json_schema())
    categories = schema["$defs"]["ComplaintCategory"]["enum"]
    assert set(categories) == {c.value for c in ComplaintCategory}


# ---------------------------------------------------------------------------
# Validators clamp model output
# ---------------------------------------------------------------------------


def _analysis(**overrides) -> ComplaintAnalysis:
    payload = {
        "category": "road",
        "severity": "high",
        "priority_score": 80,
        "summary": "Deep pothole in the left lane.",
        "department": "PWD",
        "suggested_action": "Patch the road surface.",
        "tags": ["road", "pothole"],
        "confidence": 0.9,
    }
    payload.update(overrides)
    return ComplaintAnalysis.model_validate(payload)


def test_priority_score_is_clamped():
    assert _analysis(priority_score=580).priority_score == 100
    assert _analysis(priority_score=-40).priority_score == 0


def test_confidence_is_clamped():
    assert _analysis(confidence=7.4).confidence == 1.0
    assert _analysis(confidence=-2).confidence == 0.0


def test_tags_are_deduplicated_lowercased_and_capped():
    analysis = _analysis(tags=["Road", "road", " POTHOLE ", "a", "b", "c", "d", "e"])
    assert analysis.tags[:3] == ["road", "pothole", "a"]
    assert len(analysis.tags) <= 5
    assert analysis.tags == [tag.lower() for tag in analysis.tags]


# ---------------------------------------------------------------------------
# Hallucination guards
# ---------------------------------------------------------------------------


def test_sanitise_drops_invented_duplicate_reference():
    candidates = [
        DuplicateCandidate(
            reference_code="BCA-2026-REAL01",
            title="Existing pothole",
            description="Same spot",
            category=ComplaintCategory.ROAD,
            status="submitted",
            distance_meters=20.0,
            age_hours=5.0,
        )
    ]
    analysis = _analysis(duplicate_of="BCA-2026-MADEUP", similar_references=["BCA-2026-ALSOFAKE"])
    cleaned = ClaudeService._sanitise(analysis, candidates)
    assert cleaned.duplicate_of is None
    assert cleaned.similar_references == []


def test_sanitise_keeps_known_reference():
    candidates = [
        DuplicateCandidate(
            reference_code="BCA-2026-REAL01",
            title="Existing pothole",
            description="Same spot",
            category=ComplaintCategory.ROAD,
            status="submitted",
            distance_meters=20.0,
            age_hours=5.0,
        )
    ]
    cleaned = ClaudeService._sanitise(_analysis(duplicate_of="BCA-2026-REAL01"), candidates)
    assert cleaned.duplicate_of == "BCA-2026-REAL01"


def test_sanitise_repairs_unknown_department_code():
    cleaned = ClaudeService._sanitise(_analysis(department="MINISTRY_OF_ROADS"), [])
    assert cleaned.department == "PWD"  # derived from the category


def test_sanitise_never_lists_the_duplicate_as_similar():
    candidates = [
        DuplicateCandidate(
            reference_code="BCA-2026-REAL01",
            title="t",
            description="d",
            category=ComplaintCategory.ROAD,
            status="submitted",
            distance_meters=10.0,
            age_hours=1.0,
        )
    ]
    cleaned = ClaudeService._sanitise(
        _analysis(duplicate_of="BCA-2026-REAL01", similar_references=["BCA-2026-REAL01"]),
        candidates,
    )
    assert cleaned.similar_references == []


# ---------------------------------------------------------------------------
# Deterministic fallback analyser
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Huge pothole on the main sadak near my house", ComplaintCategory.ROAD),
        ("Kachra piling up, the dustbin has not been emptied", ComplaintCategory.GARBAGE),
        ("Street light pole is dark every night", ComplaintCategory.STREETLIGHT),
        ("Water pipeline leaking, no paani since morning", ComplaintCategory.WATER),
        ("Traffic signal at the junction is not working", ComplaintCategory.TRAFFIC),
        ("The naali is blocked and sewage is overflowing", ComplaintCategory.DRAINAGE),
        ("Completely unrelated municipal question", ComplaintCategory.OTHER),
    ],
)
def test_fallback_categorises_common_reports(text, expected):
    analysis = heuristic_analysis(title=text, description=text)
    assert analysis.category is expected


def test_fallback_flags_life_threatening_reports_as_critical():
    analysis = heuristic_analysis(
        title="Live wire hanging over the footpath",
        description="An exposed live wire is touching the railing and could electrocute someone.",
    )
    assert analysis.severity is ComplaintSeverity.CRITICAL
    assert analysis.priority_score >= 85


def test_fallback_respects_the_citizen_category_hint():
    analysis = heuristic_analysis(
        title="Something is wrong on my street",
        description="There is a problem here that needs municipal attention soon.",
        category_hint=ComplaintCategory.TRAFFIC,
    )
    assert analysis.category is ComplaintCategory.TRAFFIC


def test_fallback_priority_rises_with_confirmations():
    kwargs = {
        "title": "Garbage not collected",
        "description": "The bin outside has been overflowing for two days now.",
    }
    alone = heuristic_analysis(**kwargs, confirmation_count=0)
    crowded = heuristic_analysis(**kwargs, confirmation_count=6)
    assert crowded.priority_score > alone.priority_score


def test_fallback_always_routes_to_a_real_department():
    from app.services.claude_service import VALID_DEPARTMENT_CODES

    for category in ComplaintCategory:
        analysis = heuristic_analysis(
            title="Issue report", description="Description of the civic issue.",
            category_hint=category,
        )
        assert analysis.department in VALID_DEPARTMENT_CODES


# ---------------------------------------------------------------------------
# Request construction and failure handling (mocked SDK)
# ---------------------------------------------------------------------------


def _service_with_mock(parse_return=None, parse_side_effect=None) -> tuple[ClaudeService, MagicMock]:
    service = ClaudeService(api_key="sk-ant-test", model="claude-opus-5", enabled=True)
    client = MagicMock()
    client.messages.parse = MagicMock(
        return_value=parse_return, side_effect=parse_side_effect
    )
    # `_client` is a cached_property; seed the cache directly.
    service.__dict__["_client"] = client
    return service, client


def _fake_response(parsed, stop_reason="end_turn", category=None):
    return SimpleNamespace(
        parsed_output=parsed,
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=category),
        model="claude-opus-5",
        usage=SimpleNamespace(input_tokens=900, output_tokens=180),
    )


def test_missing_api_key_uses_fallback_without_calling_the_api():
    service = ClaudeService(api_key=None, enabled=True)
    result = service.analyze_complaint(
        title="Pothole on the sadak", description="A deep pothole has formed here."
    )
    assert result.status is AIAnalysisStatus.FALLBACK
    assert result.analysis.category is ComplaintCategory.ROAD
    assert result.model is None


def test_ai_disabled_reports_skipped():
    service = ClaudeService(api_key="sk-ant-test", enabled=False)
    result = service.analyze_complaint(title="Pothole", description="Deep pothole here.")
    assert result.status is AIAnalysisStatus.SKIPPED


def test_successful_analysis_is_returned_and_marked_completed():
    expected = _analysis()
    service, client = _service_with_mock(parse_return=_fake_response(expected))

    result = service.analyze_complaint(
        title="Large pothole near the underbridge",
        description="A deep pothole in the left lane, dangerous for two-wheelers.",
        latitude=23.2331,
        longitude=77.4344,
    )

    assert result.status is AIAnalysisStatus.COMPLETED
    assert result.analysis.category is ComplaintCategory.ROAD
    assert result.model == "claude-opus-5"
    assert client.messages.parse.call_count == 1


def test_request_uses_the_intended_model_and_parameters():
    service, client = _service_with_mock(parse_return=_fake_response(_analysis()))
    service.analyze_complaint(title="Pothole here", description="A deep pothole formed.")

    kwargs = client.messages.parse.call_args.kwargs
    assert kwargs["model"] == "claude-opus-5"
    assert kwargs["output_format"] is ComplaintAnalysis
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert "effort" in kwargs["output_config"]
    # Stable system prefix is marked cacheable.
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kwargs["max_tokens"] > 0


def test_duplicate_candidates_are_included_in_the_prompt():
    service, client = _service_with_mock(parse_return=_fake_response(_analysis()))
    candidates = [
        DuplicateCandidate(
            reference_code="BCA-2026-REAL01",
            title="Pothole already reported",
            description="Same pothole, reported yesterday.",
            category=ComplaintCategory.ROAD,
            status="submitted",
            distance_meters=12.5,
            age_hours=20.0,
        )
    ]
    service.analyze_complaint(
        title="Pothole near underbridge",
        description="Deep pothole in the left lane here.",
        latitude=23.2331,
        longitude=77.4344,
        candidates=candidates,
    )
    prompt = client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "BCA-2026-REAL01" in prompt
    assert "nearby_open_complaints" in prompt


def test_prompt_states_when_there_are_no_candidates():
    service, client = _service_with_mock(parse_return=_fake_response(_analysis()))
    service.analyze_complaint(title="Pothole here", description="A deep pothole formed.")
    prompt = client.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert "No nearby open complaints" in prompt


def test_refusal_falls_back_instead_of_raising():
    service, _ = _service_with_mock(
        parse_return=_fake_response(None, stop_reason="refusal", category="cyber")
    )
    result = service.analyze_complaint(
        title="Garbage dump near the lake",
        description="Waste is being dumped into the lake every night.",
    )
    assert result.status is AIAnalysisStatus.FALLBACK
    assert result.error is not None and "refusal" in result.error
    assert result.analysis.category is ComplaintCategory.GARBAGE


def test_unparsable_reply_falls_back():
    service, _ = _service_with_mock(
        parse_return=_fake_response(None, stop_reason="max_tokens")
    )
    result = service.analyze_complaint(
        title="Street light out", description="The street light pole is dark at night."
    )
    assert result.status is AIAnalysisStatus.FALLBACK
    assert "max_tokens" in (result.error or "")


def test_transport_error_falls_back():
    service, _ = _service_with_mock(parse_side_effect=RuntimeError("connection reset"))
    result = service.analyze_complaint(
        title="Water pipeline leak", description="Water has been leaking from the pipeline."
    )
    assert result.status is AIAnalysisStatus.FALLBACK
    assert "RuntimeError" in (result.error or "")
    assert result.analysis.category is ComplaintCategory.WATER


def test_hallucinated_reference_is_stripped_end_to_end():
    service, _ = _service_with_mock(
        parse_return=_fake_response(_analysis(duplicate_of="BCA-2026-GHOST"))
    )
    result = service.analyze_complaint(
        title="Pothole here", description="A deep pothole has formed on the road."
    )
    assert result.status is AIAnalysisStatus.COMPLETED
    assert result.analysis.duplicate_of is None


# ---------------------------------------------------------------------------
# Briefing
# ---------------------------------------------------------------------------


def test_briefing_falls_back_without_a_key():
    service = ClaudeService(api_key=None, enabled=True)
    metrics = {
        "new_complaints": 12,
        "open_complaints": 40,
        "resolved_in_window": 5,
        "critical_open": 2,
        "top_category": "drainage",
        "city_health_score": 61.2,
        "unassigned_complaints": 3,
        "sla_breached_open": 4,
    }
    result = service.generate_admin_briefing(metrics, window_hours=24)
    assert result.status is AIAnalysisStatus.FALLBACK
    assert "12" in result.briefing and "drainage" in result.briefing
    assert any("critical" in item for item in result.priorities)


def test_briefing_uses_claude_when_available():
    draft = _BriefingDraft(
        headline="Drainage complaints doubled overnight",
        briefing="## Overview\nDrainage reports are up sharply.",
        priorities=["De-silt the Habibganj drain"],
        watchlist=["Monsoon forecast"],
    )
    service, client = _service_with_mock(parse_return=_fake_response(draft))
    result = service.generate_admin_briefing({"new_complaints": 9}, window_hours=24)

    assert result.status is AIAnalysisStatus.COMPLETED
    assert result.headline == "Drainage complaints doubled overnight"
    assert result.priorities == ["De-silt the Habibganj drain"]
    assert client.messages.parse.call_args.kwargs["output_format"] is _BriefingDraft
