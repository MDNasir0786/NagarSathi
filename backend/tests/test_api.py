"""API tests: authentication, role-based access, complaint lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC

from tests.conftest import BHOPAL, BHOPAL_NEAR, auth

# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_reports_dependencies(client):
    body = client.get("/ready").json()
    assert body["database"] is True
    assert body["auth_configured"] is True


def test_openapi_declares_the_bearer_scheme(client):
    spec = client.get("/openapi.json").json()
    schemes = spec["components"]["securitySchemes"]
    assert "SupabaseBearer" in schemes
    assert schemes["SupabaseBearer"]["scheme"] == "bearer"


def test_swagger_ui_is_served(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_protected_route_requires_a_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_malformed_token_is_rejected(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer nonsense.token.value"}
    )
    assert response.status_code == 401


def test_token_signed_with_the_wrong_secret_is_rejected(client):
    from datetime import datetime, timedelta

    import jwt

    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "attacker@example.com",
            "aud": "authenticated",
            "iss": "https://test.local/auth/v1",
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        "not-the-real-secret-but-long-enough-to-avoid-a-key-length-warning",
        algorithm="HS256",
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_signature"


def test_expired_token_is_rejected(client):
    from datetime import datetime, timedelta

    import jwt

    from tests.conftest import TEST_SECRET

    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "stale@example.com",
            "aud": "authenticated",
            "iss": "https://test.local/auth/v1",
            "exp": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"


def test_first_call_provisions_a_citizen_profile(client, citizen_headers):
    response = client.post("/api/v1/auth/sync", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "citizen"
    assert body["email"] == "citizen@example.com"


def test_signup_can_never_produce_an_admin(client):
    """Anyone can sign up, but only ADMIN_EMAILS yields the admin role."""
    response = client.post("/api/v1/auth/sync", headers=auth("random.person@example.com"))
    assert response.status_code == 200
    assert response.json()["role"] == "citizen"


def test_allowlisted_email_becomes_admin(client, admin_headers):
    response = client.post("/api/v1/auth/sync", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_me_includes_stats_and_permissions(client, citizen_headers):
    body = client.get("/api/v1/auth/me", headers=citizen_headers).json()
    assert "stats" in body and "permissions" in body
    assert "complaint:create" in body["permissions"]
    assert "user:manage" not in body["permissions"]


def test_admin_permissions_are_broader(client, admin_headers):
    body = client.get("/api/v1/auth/me", headers=admin_headers).json()
    assert "user:manage" in body["permissions"]
    assert "ai:briefing" in body["permissions"]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def test_profile_update_and_read(client, citizen_headers):
    updated = client.patch(
        "/api/v1/profile",
        headers=citizen_headers,
        json={"full_name": "Aarav Sharma", "ward": "Ward 32", "phone": "+919812345678"},
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Aarav Sharma"

    fetched = client.get("/api/v1/profile", headers=citizen_headers).json()
    assert fetched["ward"] == "Ward 32"


def test_profile_cannot_self_assign_a_role(client, citizen_headers):
    response = client.patch(
        "/api/v1/profile", headers=citizen_headers, json={"role": "admin"}
    )
    assert response.status_code == 422
    assert client.get("/api/v1/profile", headers=citizen_headers).json()["role"] == "citizen"


def test_profile_cannot_self_activate_or_pick_department(client, citizen_headers):
    for payload in ({"is_active": True}, {"department_id": str(uuid.uuid4())}):
        assert (
            client.patch("/api/v1/profile", headers=citizen_headers, json=payload).status_code
            == 422
        )


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------


def _file_complaint(client, headers, **overrides) -> dict:
    payload = {
        "title": "Large pothole near Habibganj underbridge",
        "description": (
            "A deep pothole has opened in the left lane after the underbridge and it "
            "floods whenever it rains, which is dangerous for two-wheelers."
        ),
        "latitude": BHOPAL[0],
        "longitude": BHOPAL[1],
        "ward": "Ward 32",
        "category_hint": "road",
    }
    payload.update(overrides)
    response = client.post("/api/v1/complaints", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_filing_a_complaint_classifies_and_routes_it(client, citizen_headers):
    body = _file_complaint(client, citizen_headers)
    complaint = body["complaint"]

    assert complaint["reference_code"].startswith("BCA-")
    assert complaint["category"] == "road"
    assert complaint["status"] in {"submitted", "duplicate"}
    assert 0 <= complaint["priority_score"] <= 100
    assert complaint["department"]["code"] == "PWD", "must be routed to Public Works"
    assert complaint["ai_analysis"]["summary"]
    assert body["ai_status"] in {"completed", "fallback", "skipped"}
    # The timeline starts with the citizen filing it.
    assert complaint["timeline"][0]["update_type"] == "created"


def test_complaint_outside_the_city_is_rejected(client, citizen_headers):
    response = client.post(
        "/api/v1/complaints",
        headers=citizen_headers,
        json={
            "title": "Pothole in another city entirely",
            "description": "This coordinate is nowhere near the Bhopal service area.",
            "latitude": 19.0760,
            "longitude": 72.8777,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "outside_service_area"


def test_complaint_validation_rejects_thin_input(client, citizen_headers):
    response = client.post(
        "/api/v1/complaints",
        headers=citizen_headers,
        json={"title": "Bad", "description": "short", "latitude": 23.2, "longitude": 77.4},
    )
    assert response.status_code == 422


def test_client_cannot_set_severity_or_priority(client, citizen_headers):
    response = client.post(
        "/api/v1/complaints",
        headers=citizen_headers,
        json={
            "title": "Trying to force a critical severity",
            "description": "A citizen should not be able to dictate severity or priority.",
            "latitude": BHOPAL[0],
            "longitude": BHOPAL[1],
            "severity": "critical",
            "priority_score": 100,
        },
    )
    assert response.status_code == 422  # extra="forbid" on the schema


def test_citizen_sees_only_their_own_complaints(client, citizen_headers, other_headers):
    _file_complaint(client, citizen_headers)
    _file_complaint(
        client,
        other_headers,
        title="Broken street light on the colony road",
        description="The street light outside the colony gate has been dark for a week now.",
        category_hint="streetlight",
    )

    mine = client.get("/api/v1/complaints", headers=citizen_headers).json()
    titles = {item["title"] for item in mine["items"]}
    assert "Broken street light on the colony road" not in titles


def test_other_citizen_cannot_read_my_complaint(client, citizen_headers, other_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.get(f"/api/v1/complaints/{complaint_id}", headers=other_headers)
    assert response.status_code == 403


def test_unknown_complaint_returns_404(client, citizen_headers):
    response = client.get(f"/api/v1/complaints/{uuid.uuid4()}", headers=citizen_headers)
    assert response.status_code == 404


def test_status_tracking_exposes_the_timeline_and_sla(client, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    body = client.get(
        f"/api/v1/complaints/{complaint_id}/status", headers=citizen_headers
    ).json()
    assert body["is_open"] is True
    assert body["sla_hours"] == 96  # PWD
    assert body["sla_due_at"] is not None
    assert body["timeline"]


def test_lookup_by_reference_code(client, citizen_headers):
    reference = _file_complaint(client, citizen_headers)["complaint"]["reference_code"]
    response = client.get(
        f"/api/v1/complaints/reference/{reference}", headers=citizen_headers
    )
    assert response.status_code == 200
    assert response.json()["reference_code"] == reference


# ---------------------------------------------------------------------------
# Nearby + confirmations
# ---------------------------------------------------------------------------


def test_nearby_finds_an_existing_open_issue(client, citizen_headers, other_headers):
    _file_complaint(
        client,
        citizen_headers,
        title="Pothole outside the community hall",
        description="A wide pothole has formed right outside the community hall gate.",
    )
    nearby = client.get(
        "/api/v1/complaints/nearby",
        headers=other_headers,
        params={"latitude": BHOPAL_NEAR[0], "longitude": BHOPAL_NEAR[1]},
    ).json()
    assert nearby, "an open complaint ~45 m away should be offered for confirmation"
    assert nearby[0]["distance_meters"] < 200
    assert nearby[0]["is_mine"] is False


def test_confirmation_raises_priority_and_is_one_per_citizen(
    client, citizen_headers, other_headers
):
    complaint = _file_complaint(
        client,
        citizen_headers,
        title="Drain blocked near the school gate",
        description="The drain outside the school gate is blocked and water is stagnating.",
        category_hint="drainage",
    )["complaint"]
    before = complaint["priority_score"]

    first = client.post(
        f"/api/v1/complaints/{complaint['id']}/confirm",
        headers=other_headers,
        json={"note": "Same problem, I walk past it daily.", "latitude": BHOPAL_NEAR[0],
              "longitude": BHOPAL_NEAR[1]},
    )
    assert first.status_code == 201
    assert first.json()["confirmation_count"] == 1
    assert first.json()["priority_score"] > before

    again = client.post(
        f"/api/v1/complaints/{complaint['id']}/confirm",
        headers=other_headers,
        json={"note": "Trying to double count."},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_confirmed"


def test_cannot_confirm_your_own_complaint(client, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.post(
        f"/api/v1/complaints/{complaint_id}/confirm", headers=citizen_headers, json={}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "own_complaint"


def test_cannot_confirm_from_far_away(client, citizen_headers, other_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.post(
        f"/api/v1/complaints/{complaint_id}/confirm",
        headers=other_headers,
        json={"latitude": 19.0760, "longitude": 72.8777},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "too_far_to_confirm"


# ---------------------------------------------------------------------------
# Admin authorisation
# ---------------------------------------------------------------------------


def test_citizens_are_locked_out_of_every_admin_route(client, citizen_headers):
    routes = [
        ("get", "/api/v1/admin/dashboard"),
        ("get", "/api/v1/admin/complaints"),
        ("get", "/api/v1/admin/departments"),
        ("get", "/api/v1/admin/users"),
        ("get", "/api/v1/analytics/departments"),
        ("get", "/api/v1/ai/admin-briefing"),
    ]
    for method, path in routes:
        response = getattr(client, method)(path, headers=citizen_headers)
        assert response.status_code == 403, f"{path} leaked to a citizen"
        assert response.json()["error"]["code"] == "admin_required"


def test_admin_routes_need_a_token_at_all(client):
    assert client.get("/api/v1/admin/dashboard").status_code == 401


def test_admin_dashboard_returns_the_expected_shape(client, admin_headers, citizen_headers):
    _file_complaint(client, citizen_headers)
    body = client.get("/api/v1/admin/dashboard", headers=admin_headers).json()
    for key in (
        "total_complaints",
        "open_complaints",
        "by_status",
        "by_category",
        "by_department",
        "city_health_score",
        "resolution_rate",
    ):
        assert key in body
    assert body["total_complaints"] >= 1
    assert 0 <= body["city_health_score"] <= 100


def test_admin_can_read_any_complaint(client, admin_headers, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.get(f"/api/v1/admin/complaints/{complaint_id}", headers=admin_headers)
    assert response.status_code == 200


def test_admin_workflow_updates_status_and_audit_trail(
    client, admin_headers, citizen_headers
):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]

    acknowledged = client.patch(
        f"/api/v1/admin/complaints/{complaint_id}",
        headers=admin_headers,
        json={"status": "acknowledged", "public_note": "Inspection scheduled."},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_at"] is not None

    # Resolving without a note is refused...
    refused = client.patch(
        f"/api/v1/admin/complaints/{complaint_id}",
        headers=admin_headers,
        json={"status": "resolved"},
    )
    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "resolution_note_required"

    # ...and accepted with one.
    resolved = client.patch(
        f"/api/v1/admin/complaints/{complaint_id}",
        headers=admin_headers,
        json={
            "status": "resolved",
            "resolution_notes": "Pothole filled with hot mix and compacted.",
        },
    )
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["resolved_at"] is not None
    assert body["resolution_hours"] is not None

    types = [entry["update_type"] for entry in body["timeline"]]
    assert "status_change" in types and "resolution_note" in types


def test_citizen_timeline_hides_internal_notes(client, admin_headers, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    client.patch(
        f"/api/v1/admin/complaints/{complaint_id}",
        headers=admin_headers,
        json={"internal_note": "Crew is short-staffed this week — internal only."},
    )

    citizen_view = client.get(
        f"/api/v1/complaints/{complaint_id}", headers=citizen_headers
    ).json()
    notes = [entry["note"] or "" for entry in citizen_view["timeline"]]
    assert not any("short-staffed" in note for note in notes)

    admin_view = client.get(
        f"/api/v1/admin/complaints/{complaint_id}", headers=admin_headers
    ).json()
    admin_notes = [entry["note"] or "" for entry in admin_view["timeline"]]
    assert any("short-staffed" in note for note in admin_notes)


def test_citizen_cannot_edit_after_acknowledgement(client, admin_headers, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    client.patch(
        f"/api/v1/admin/complaints/{complaint_id}",
        headers=admin_headers,
        json={"status": "acknowledged"},
    )
    response = client.patch(
        f"/api/v1/complaints/{complaint_id}",
        headers=citizen_headers,
        json={"landmark": "Trying to edit late"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "complaint_locked"


def test_admin_can_add_evidence(client, admin_headers, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.post(
        f"/api/v1/admin/complaints/{complaint_id}/evidence",
        headers=admin_headers,
        json={
            "before_image_url": "https://cdn.example.com/before.jpg",
            "after_image_url": "https://cdn.example.com/after.jpg",
        },
    )
    assert response.status_code == 200
    assert response.json()["after_image_url"] == "https://cdn.example.com/after.jpg"


def test_evidence_rejects_a_non_http_url(client, admin_headers, citizen_headers):
    complaint_id = _file_complaint(client, citizen_headers)["complaint"]["id"]
    response = client.post(
        f"/api/v1/admin/complaints/{complaint_id}/evidence",
        headers=admin_headers,
        json={"after_image_url": "javascript:alert(1)"},
    )
    assert response.status_code == 422


def test_admin_search_and_filters(client, admin_headers, citizen_headers):
    _file_complaint(
        client,
        citizen_headers,
        title="Garbage bin overflowing at the market",
        description="The market bin has not been cleared and waste is spilling onto the path.",
        category_hint="garbage",
    )
    filtered = client.get(
        "/api/v1/admin/complaints",
        headers=admin_headers,
        params={"category": "garbage", "search": "market", "sort": "-priority_score"},
    ).json()
    assert filtered["items"]
    assert all(item["category"] == "garbage" for item in filtered["items"])


def test_pagination_metadata(client, admin_headers):
    page = client.get(
        "/api/v1/admin/complaints", headers=admin_headers, params={"limit": 2, "offset": 0}
    ).json()
    assert len(page["items"]) <= 2
    assert page["pagination"]["limit"] == 2
    assert "has_more" in page["pagination"]


def test_page_size_is_capped(client, admin_headers):
    response = client.get(
        "/api/v1/admin/complaints", headers=admin_headers, params={"limit": 5000}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Role management
# ---------------------------------------------------------------------------


def test_admin_can_promote_and_demote(client, admin_headers):
    client.post("/api/v1/auth/sync", headers=auth("promote.me@example.com"))
    users = client.get(
        "/api/v1/admin/users", headers=admin_headers, params={"search": "promote.me"}
    ).json()
    user_id = users["items"][0]["id"]

    promoted = client.post(
        f"/api/v1/admin/users/{user_id}/role", headers=admin_headers, json={"role": "admin"}
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    demoted = client.post(
        f"/api/v1/admin/users/{user_id}/role", headers=admin_headers, json={"role": "citizen"}
    )
    assert demoted.status_code == 200
    assert demoted.json()["role"] == "citizen"


def test_admin_cannot_demote_themselves(client, admin_headers):
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()["profile"]
    response = client.post(
        f"/api/v1/admin/users/{me['id']}/role",
        headers=admin_headers,
        json={"role": "citizen"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "self_demotion"


def test_deactivated_user_is_locked_out(client, admin_headers):
    email = "to.disable@example.com"
    client.post("/api/v1/auth/sync", headers=auth(email))
    users = client.get(
        "/api/v1/admin/users", headers=admin_headers, params={"search": "to.disable"}
    ).json()
    user_id = users["items"][0]["id"]

    client.post(
        f"/api/v1/admin/users/{user_id}/active",
        headers=admin_headers,
        json={"is_active": False},
    )
    blocked = client.get("/api/v1/auth/me", headers=auth(email))
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "account_disabled"

    client.post(
        f"/api/v1/admin/users/{user_id}/active",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert client.get("/api/v1/auth/me", headers=auth(email)).status_code == 200


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------


def test_departments_are_seeded(client, admin_headers):
    departments = client.get("/api/v1/admin/departments", headers=admin_headers).json()
    codes = {department["code"] for department in departments}
    assert {"PWD", "SWM", "ELEC", "WATER", "TRAFFIC", "DRAIN", "GENERAL"} <= codes


def test_duplicate_department_code_is_rejected(client, admin_headers):
    response = client.post(
        "/api/v1/admin/departments",
        headers=admin_headers,
        json={"name": "Public Works Department", "code": "PWD"},
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Analytics + AI
# ---------------------------------------------------------------------------


def test_analytics_endpoints_are_available_to_citizens(client, citizen_headers):
    for path in ("/api/v1/analytics/hotspots", "/api/v1/analytics/trends",
                 "/api/v1/analytics/categories", "/api/v1/analytics/city-health"):
        assert client.get(path, headers=citizen_headers).status_code == 200


def test_hotspots_cluster_repeated_reports(client, citizen_headers, other_headers, admin_headers):
    for index in range(3):
        _file_complaint(
            client,
            citizen_headers if index % 2 else other_headers,
            title=f"Pothole cluster report {index}",
            description="Another pothole in the same stretch of road as the earlier reports.",
            latitude=BHOPAL[0] + index * 0.0001,
            longitude=BHOPAL[1] + index * 0.0001,
        )
    body = client.get(
        "/api/v1/analytics/hotspots",
        headers=admin_headers,
        params={"min_complaints": 2, "grid_meters": 500},
    ).json()
    assert body["total_hotspots"] >= 1
    hotspot = body["hotspots"][0]
    assert hotspot["complaint_count"] >= 2
    assert 0 <= hotspot["intensity"] <= 1
    assert hotspot["sample_complaints"]


def test_city_health_score_is_bounded_with_components(client, citizen_headers):
    body = client.get("/api/v1/analytics/city-health", headers=citizen_headers).json()
    assert 0 <= body["score"] <= 100
    assert body["grade"]
    assert body["trend"] in {"improving", "worsening", "stable"}
    assert set(body["components"]) == {
        "resolution", "speed", "backlog", "severity", "engagement"
    }


def test_department_performance_is_admin_only(client, admin_headers):
    body = client.get("/api/v1/analytics/departments", headers=admin_headers).json()
    assert body["departments"]
    for department in body["departments"]:
        assert 0 <= department["performance_score"] <= 100


def test_ai_analyze_returns_a_full_verdict(client, citizen_headers):
    response = client.post(
        "/api/v1/ai/analyze-complaint",
        headers=citizen_headers,
        json={
            "title": "Sewage overflowing near the school gate",
            "description": (
                "The main drain outside the primary school has been overflowing since "
                "yesterday and children walk through the sewage to reach the gate."
            ),
            "latitude": BHOPAL[0],
            "longitude": BHOPAL[1],
        },
    )
    assert response.status_code == 200
    body = response.json()
    analysis = body["analysis"]
    assert analysis["category"] in {
        "road", "garbage", "streetlight", "water", "traffic", "drainage", "other"
    }
    assert analysis["severity"] in {"low", "medium", "high", "critical"}
    assert 0 <= analysis["priority_score"] <= 100
    assert analysis["summary"] and analysis["suggested_action"]
    assert body["status"] in {"completed", "fallback", "skipped"}
    assert body["department_name"]


def test_ai_briefing_for_admin(client, admin_headers):
    response = client.get(
        "/api/v1/ai/admin-briefing", headers=admin_headers, params={"window_hours": 24}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["headline"] and body["briefing"]
    assert body["status"] in {"completed", "fallback"}
    assert "open_complaints" in body["metrics_snapshot"]


def test_ai_response_never_leaks_the_api_key(client, citizen_headers):
    response = client.post(
        "/api/v1/ai/analyze-complaint",
        headers=citizen_headers,
        json={
            "title": "Street light not working on the main road",
            "description": "The street light outside the gate has been dark for five nights.",
        },
    )
    assert "sk-ant" not in response.text
    assert "api_key" not in response.text.lower()
