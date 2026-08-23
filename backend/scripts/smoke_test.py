#!/usr/bin/env python
"""End-to-end check of every documented endpoint against a running server.

This is the scripted equivalent of clicking through Swagger: it drives the real
HTTP surface (auth, validation, role checks, AI fallback) and asserts the status
code of each call.

    # terminal 1
    uvicorn app.main:app --port 8000
    # terminal 2
    python scripts/smoke_test.py --base-url http://localhost:8000

Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.dev_token import mint

CITIZEN_EMAIL = "smoke.citizen@example.com"
NEIGHBOUR_EMAIL = "smoke.neighbour@example.com"
ADMIN_EMAIL = "admin@bhopalcivicai.in"  # must be listed in ADMIN_EMAILS

# Two points ~40 m apart near Habibganj, Bhopal, and one far across town.
SPOT_A = (23.23310, 77.43440)
SPOT_A_NEAR = (23.23345, 77.43455)
SPOT_B = (23.27980, 77.39810)
OUTSIDE_CITY = (19.07600, 72.87770)  # Mumbai


class Runner:
    def __init__(self, base_url: str, verbose: bool = False) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=60.0)
        self.verbose = verbose
        self.passed = 0
        self.failed: list[str] = []
        self.results: list[tuple[str, str, str, int, int, bool]] = []

    def call(
        self,
        name: str,
        method: str,
        path: str,
        *,
        expect: int | tuple[int, ...],
        token: str | None = None,
        json: Any = None,
        params: dict | None = None,
        raw_headers: dict | None = None,
    ) -> httpx.Response | None:
        headers = dict(raw_headers or {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            response = self.client.request(
                method, path, json=json, params=params, headers=headers
            )
        except httpx.HTTPError as exc:
            self.failed.append(f"{name}: transport error {exc}")
            self.results.append((name, method, path, -1, -1, False))
            print(f"  FAIL  {name}: transport error {exc}")
            return None

        expected = (expect,) if isinstance(expect, int) else expect
        ok = response.status_code in expected
        self.results.append(
            (name, method, path, expected[0], response.status_code, ok)
        )
        if ok:
            self.passed += 1
            if self.verbose:
                print(f"  ok    {method:6} {path} -> {response.status_code}  [{name}]")
        else:
            body = response.text[:400].replace("\n", " ")
            self.failed.append(
                f"{name}: expected {expected}, got {response.status_code} — {body}"
            )
            print(
                f"  FAIL  {method:6} {path} -> {response.status_code} "
                f"(expected {expected})  [{name}]\n        {body}"
            )
        return response

    def summary(self) -> int:
        total = self.passed + len(self.failed)
        print("\n" + "=" * 78)
        print(f"  {self.passed}/{total} checks passed")
        if self.failed:
            print(f"  {len(self.failed)} FAILED:")
            for failure in self.failed:
                print(f"    - {failure}")
            print("=" * 78)
            return 1
        print("  ALL ENDPOINT CHECKS PASSED")
        print("=" * 78)
        return 0


def run(base_url: str, verbose: bool) -> int:
    r = Runner(base_url, verbose)

    citizen = mint(CITIZEN_EMAIL, "Smoke Citizen", 6, None)
    neighbour = mint(NEIGHBOUR_EMAIL, "Smoke Neighbour", 6, None)
    admin = mint(ADMIN_EMAIL, "City Admin", 6, None)

    # ---------------------------------------------------------------- system
    print("\n[system]")
    r.call("health", "GET", "/health", expect=200)
    r.call("ready", "GET", "/ready", expect=200)
    r.call("root", "GET", "/", expect=200)
    r.call("openapi", "GET", "/openapi.json", expect=200)
    r.call("swagger ui", "GET", "/docs", expect=200)
    r.call("redoc", "GET", "/redoc", expect=200)

    # ------------------------------------------------------------------ auth
    print("\n[auth]")
    r.call("auth: no token -> 401", "GET", "/api/v1/auth/me", expect=401)
    r.call(
        "auth: garbage token -> 401",
        "GET",
        "/api/v1/auth/me",
        expect=401,
        raw_headers={"Authorization": "Bearer not.a.jwt"},
    )
    r.call(
        "auth: wrong scheme -> 401",
        "GET",
        "/api/v1/auth/me",
        expect=401,
        raw_headers={"Authorization": f"Basic {citizen}"},
    )
    sync = r.call("auth: citizen sync", "POST", "/api/v1/auth/sync", expect=200, token=citizen)
    if sync is not None and sync.status_code == 200:
        assert sync.json()["role"] == "citizen", "signup must never yield admin"
    r.call("auth: neighbour sync", "POST", "/api/v1/auth/sync", expect=200, token=neighbour)
    admin_sync = r.call("auth: admin sync", "POST", "/api/v1/auth/sync", expect=200, token=admin)
    if admin_sync is not None and admin_sync.status_code == 200:
        role = admin_sync.json()["role"]
        assert role == "admin", f"ADMIN_EMAILS allow-list did not apply (role={role})"
    r.call("auth: me", "GET", "/api/v1/auth/me", expect=200, token=citizen)
    r.call("auth: verify", "GET", "/api/v1/auth/verify", expect=200, token=citizen)

    # --------------------------------------------------------------- profile
    print("\n[profile]")
    r.call("profile: get", "GET", "/api/v1/profile", expect=200, token=citizen)
    r.call(
        "profile: upsert",
        "POST",
        "/api/v1/profile",
        expect=200,
        token=citizen,
        json={
            "full_name": "Aarav Sharma",
            "phone": "+919812345678",
            "ward": "Ward 32",
            "address": "12 Shakti Nagar, Bhopal",
        },
    )
    r.call(
        "profile: patch",
        "PATCH",
        "/api/v1/profile",
        expect=200,
        token=citizen,
        json={"ward": "Ward 33", "language": "hi"},
    )
    r.call(
        "profile: reject role escalation",
        "PATCH",
        "/api/v1/profile",
        expect=422,
        token=citizen,
        json={"role": "admin"},
    )
    r.call("profile: stats", "GET", "/api/v1/profile/stats", expect=200, token=citizen)

    # ------------------------------------------------------------ complaints
    print("\n[complaints]")
    r.call(
        "complaints: nearby (empty ok)",
        "GET",
        "/api/v1/complaints/nearby",
        expect=200,
        token=citizen,
        params={"latitude": SPOT_A[0], "longitude": SPOT_A[1], "radius_meters": 500},
    )
    created = r.call(
        "complaints: create pothole",
        "POST",
        "/api/v1/complaints",
        expect=201,
        token=citizen,
        json={
            "title": "Large pothole near Habibganj underbridge",
            "description": (
                "A deep pothole has opened in the left lane just after the underbridge. "
                "Two-wheelers swerve into traffic to avoid it and it floods when it rains. "
                "It is dangerous at night because the street light there is also out."
            ),
            "latitude": SPOT_A[0],
            "longitude": SPOT_A[1],
            "address": "Habibganj Underbridge, Bhopal",
            "landmark": "Opposite the bus stop",
            "ward": "Ward 32",
            "category_hint": "road",
        },
    )
    complaint_id = None
    reference_code = None
    if created is not None and created.status_code == 201:
        body = created.json()
        complaint_id = body["complaint"]["id"]
        reference_code = body["complaint"]["reference_code"]
        assert body["ai_status"] in {"completed", "fallback", "skipped"}
        assert body["complaint"]["department"] is not None, "complaint was not routed"

    second = r.call(
        "complaints: create garbage (other side of town)",
        "POST",
        "/api/v1/complaints",
        expect=201,
        token=citizen,
        json={
            "title": "Overflowing garbage bin attracting stray dogs",
            "description": (
                "The community bin by the park gate has not been emptied for four days. "
                "Waste is spilling across the footpath and stray dogs scatter it onto the road."
            ),
            "latitude": SPOT_B[0],
            "longitude": SPOT_B[1],
            "ward": "Ward 14",
        },
    )
    second_id = second.json()["complaint"]["id"] if second and second.status_code == 201 else None

    r.call(
        "complaints: reject location outside city",
        "POST",
        "/api/v1/complaints",
        expect=422,
        token=citizen,
        json={
            "title": "Pothole reported from another city",
            "description": "This location is far outside the Bhopal service area entirely.",
            "latitude": OUTSIDE_CITY[0],
            "longitude": OUTSIDE_CITY[1],
        },
    )
    r.call(
        "complaints: reject short title",
        "POST",
        "/api/v1/complaints",
        expect=422,
        token=citizen,
        json={
            "title": "Pot",
            "description": "Too short a title should fail validation cleanly.",
            "latitude": SPOT_A[0],
            "longitude": SPOT_A[1],
        },
    )
    r.call(
        "complaints: reject bad coordinates",
        "POST",
        "/api/v1/complaints",
        expect=422,
        token=citizen,
        json={
            "title": "Invalid coordinates complaint",
            "description": "Latitude is out of the valid WGS84 range for this test.",
            "latitude": 200.0,
            "longitude": 77.4,
        },
    )
    r.call("complaints: no token -> 401", "GET", "/api/v1/complaints", expect=401)
    r.call("complaints: list mine", "GET", "/api/v1/complaints", expect=200, token=citizen)
    r.call(
        "complaints: list filtered",
        "GET",
        "/api/v1/complaints",
        expect=200,
        token=citizen,
        params={"status": ["submitted", "assigned"], "category": "road", "limit": 5},
    )
    r.call(
        "complaints: list searched",
        "GET",
        "/api/v1/complaints",
        expect=200,
        token=citizen,
        params={"search": "pothole", "sort": "-priority_score"},
    )

    if complaint_id:
        r.call(
            "complaints: detail",
            "GET",
            f"/api/v1/complaints/{complaint_id}",
            expect=200,
            token=citizen,
        )
        r.call(
            "complaints: track status",
            "GET",
            f"/api/v1/complaints/{complaint_id}/status",
            expect=200,
            token=citizen,
        )
        r.call(
            "complaints: citizen edit",
            "PATCH",
            f"/api/v1/complaints/{complaint_id}",
            expect=200,
            token=citizen,
            json={"landmark": "Next to the tea stall, opposite the bus stop"},
        )
        r.call(
            "complaints: other citizen cannot read -> 403",
            "GET",
            f"/api/v1/complaints/{complaint_id}",
            expect=403,
            token=neighbour,
        )
        r.call(
            "complaints: own complaint cannot be confirmed -> 409",
            "POST",
            f"/api/v1/complaints/{complaint_id}/confirm",
            expect=409,
            token=citizen,
            json={"note": "This is my own report."},
        )
        r.call(
            "complaints: neighbour confirms",
            "POST",
            f"/api/v1/complaints/{complaint_id}/confirm",
            expect=201,
            token=neighbour,
            json={
                "note": "I hit this pothole this morning too.",
                "latitude": SPOT_A_NEAR[0],
                "longitude": SPOT_A_NEAR[1],
            },
        )
        r.call(
            "complaints: duplicate confirm -> 409",
            "POST",
            f"/api/v1/complaints/{complaint_id}/confirm",
            expect=409,
            token=neighbour,
            json={"note": "Trying twice."},
        )
        r.call(
            "complaints: confirm from far away -> 422",
            "POST",
            f"/api/v1/complaints/{second_id or complaint_id}/confirm",
            expect=422,
            token=neighbour,
            json={"latitude": OUTSIDE_CITY[0], "longitude": OUTSIDE_CITY[1]},
        )
    if reference_code:
        r.call(
            "complaints: lookup by reference",
            "GET",
            f"/api/v1/complaints/reference/{reference_code}",
            expect=200,
            token=citizen,
        )
    r.call(
        "complaints: unknown id -> 404",
        "GET",
        f"/api/v1/complaints/{uuid.uuid4()}",
        expect=404,
        token=citizen,
    )
    r.call(
        "complaints: nearby now finds one",
        "GET",
        "/api/v1/complaints/nearby",
        expect=200,
        token=neighbour,
        params={"latitude": SPOT_A_NEAR[0], "longitude": SPOT_A_NEAR[1]},
    )

    # ----------------------------------------------------------------- admin
    print("\n[admin]")
    r.call(
        "admin: citizen blocked from dashboard -> 403",
        "GET",
        "/api/v1/admin/dashboard",
        expect=403,
        token=citizen,
    )
    r.call("admin: dashboard", "GET", "/api/v1/admin/dashboard", expect=200, token=admin)
    r.call(
        "admin: dashboard windowed",
        "GET",
        "/api/v1/admin/dashboard",
        expect=200,
        token=admin,
        params={"window_days": 7},
    )
    r.call("admin: list complaints", "GET", "/api/v1/admin/complaints", expect=200, token=admin)
    r.call(
        "admin: filter + search complaints",
        "GET",
        "/api/v1/admin/complaints",
        expect=200,
        token=admin,
        params={
            "status": "submitted",
            "category": ["road", "garbage"],
            "search": "bin",
            "sort": "-priority_score",
            "limit": 10,
        },
    )
    r.call(
        "admin: unassigned filter",
        "GET",
        "/api/v1/admin/complaints",
        expect=200,
        token=admin,
        params={"unassigned_only": True},
    )

    departments = r.call(
        "admin: list departments", "GET", "/api/v1/admin/departments", expect=200, token=admin
    )
    pwd_id = None
    if departments is not None and departments.status_code == 200:
        for department in departments.json():
            if department["code"] == "PWD":
                pwd_id = department["id"]
    code_suffix = uuid.uuid4().hex[:4].upper()
    new_department = r.call(
        "admin: create department",
        "POST",
        "/api/v1/admin/departments",
        expect=201,
        token=admin,
        json={
            "name": f"Parks and Gardens {code_suffix}",
            "code": f"PARKS{code_suffix}",
            "description": "Public parks, gardens and tree maintenance.",
            "categories": ["other"],
            "sla_hours": 120,
        },
    )
    if new_department is not None and new_department.status_code == 201:
        r.call(
            "admin: update department",
            "PATCH",
            f"/api/v1/admin/departments/{new_department.json()['id']}",
            expect=200,
            token=admin,
            json={"sla_hours": 96, "contact_phone": "+917552550000"},
        )

    if complaint_id:
        r.call(
            "admin: complaint detail",
            "GET",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=200,
            token=admin,
        )
        r.call(
            "admin: acknowledge",
            "PATCH",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=200,
            token=admin,
            json={
                "status": "acknowledged",
                "public_note": "Inspection scheduled for tomorrow morning.",
            },
        )
        if pwd_id:
            r.call(
                "admin: assign department + priority",
                "PATCH",
                f"/api/v1/admin/complaints/{complaint_id}",
                expect=200,
                token=admin,
                json={
                    "department_id": pwd_id,
                    "priority_score": 91,
                    "severity": "high",
                    "internal_note": "Crew 4 has the asphalt mix.",
                },
            )
        r.call(
            "admin: resolve without note -> 422",
            "PATCH",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=422,
            token=admin,
            json={"status": "resolved"},
        )
        r.call(
            "admin: resolve with note",
            "PATCH",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=200,
            token=admin,
            json={
                "status": "resolved",
                "resolution_notes": "Pothole filled with hot mix and compacted; lane reopened.",
                "public_note": "Repair completed and verified on site.",
            },
        )
        r.call(
            "admin: attach evidence",
            "POST",
            f"/api/v1/admin/complaints/{complaint_id}/evidence",
            expect=200,
            token=admin,
            json={
                "before_image_url": "https://example.supabase.co/storage/v1/object/public/evidence/before.jpg",
                "after_image_url": "https://example.supabase.co/storage/v1/object/public/evidence/after.jpg",
                "note": "Before and after the patch work.",
            },
        )
        r.call(
            "admin: evidence requires a url -> 422",
            "POST",
            f"/api/v1/admin/complaints/{complaint_id}/evidence",
            expect=422,
            token=admin,
            json={"note": "no urls supplied"},
        )
        r.call(
            "admin: reanalyze (persist)",
            "POST",
            f"/api/v1/admin/complaints/{complaint_id}/reanalyze",
            expect=200,
            token=admin,
            params={"apply": True},
        )
        r.call(
            "admin: reanalyze (dry run)",
            "POST",
            f"/api/v1/admin/complaints/{complaint_id}/reanalyze",
            expect=200,
            token=admin,
            params={"apply": False},
        )
        r.call(
            "admin: reject empty patch -> 422",
            "PATCH",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=422,
            token=admin,
            json={},
        )
        r.call(
            "admin: reject unknown field -> 422",
            "PATCH",
            f"/api/v1/admin/complaints/{complaint_id}",
            expect=422,
            token=admin,
            json={"reference_code": "BCA-2026-HACKED"},
        )

    if second_id:
        r.call(
            "admin: mark duplicate",
            "PATCH",
            f"/api/v1/admin/complaints/{second_id}",
            expect=200,
            token=admin,
            json={"duplicate_of_id": complaint_id},
        )

    # ----------------------------------------------------------- users/roles
    print("\n[users & roles]")
    users = r.call("admin: list users", "GET", "/api/v1/admin/users", expect=200, token=admin)
    r.call(
        "admin: filter users by role",
        "GET",
        "/api/v1/admin/users",
        expect=200,
        token=admin,
        params={"role": "citizen", "search": "smoke"},
    )
    neighbour_id = None
    if users is not None and users.status_code == 200:
        for item in users.json()["items"]:
            if item["email"] == NEIGHBOUR_EMAIL:
                neighbour_id = item["id"]
    if neighbour_id:
        r.call(
            "admin: promote citizen to admin",
            "POST",
            f"/api/v1/admin/users/{neighbour_id}/role",
            expect=200,
            token=admin,
            json={"role": "admin"},
        )
        r.call(
            "admin: demote back to citizen",
            "POST",
            f"/api/v1/admin/users/{neighbour_id}/role",
            expect=200,
            token=admin,
            json={"role": "citizen"},
        )
        r.call(
            "admin: deactivate then reactivate",
            "POST",
            f"/api/v1/admin/users/{neighbour_id}/active",
            expect=200,
            token=admin,
            json={"is_active": False},
        )
        r.call(
            "admin: reactivate user",
            "POST",
            f"/api/v1/admin/users/{neighbour_id}/active",
            expect=200,
            token=admin,
            json={"is_active": True},
        )
    r.call(
        "admin: citizen cannot grant roles -> 403",
        "POST",
        f"/api/v1/admin/users/{neighbour_id or uuid.uuid4()}/role",
        expect=403,
        token=citizen,
        json={"role": "admin"},
    )
    r.call(
        "admin: cannot self-demote -> 409",
        "POST",
        f"/api/v1/admin/users/{admin_sync.json()['id'] if admin_sync else uuid.uuid4()}/role",
        expect=409,
        token=admin,
        json={"role": "citizen"},
    )

    # ------------------------------------------------------------- analytics
    print("\n[analytics]")
    r.call("analytics: hotspots", "GET", "/api/v1/analytics/hotspots", expect=200, token=citizen)
    r.call(
        "analytics: hotspots tuned",
        "GET",
        "/api/v1/analytics/hotspots",
        expect=200,
        token=admin,
        params={"window_days": 30, "grid_meters": 250, "min_complaints": 2, "open_only": True},
    )
    r.call("analytics: trends", "GET", "/api/v1/analytics/trends", expect=200, token=citizen)
    r.call(
        "analytics: trends weekly",
        "GET",
        "/api/v1/analytics/trends",
        expect=200,
        token=admin,
        params={"granularity": "week", "window_days": 90},
    )
    r.call(
        "analytics: bad granularity -> 422",
        "GET",
        "/api/v1/analytics/trends",
        expect=422,
        token=admin,
        params={"granularity": "fortnight"},
    )
    r.call("analytics: categories", "GET", "/api/v1/analytics/categories", expect=200, token=citizen)
    r.call("analytics: city health", "GET", "/api/v1/analytics/city-health", expect=200, token=citizen)
    r.call(
        "analytics: departments (admin)",
        "GET",
        "/api/v1/analytics/departments",
        expect=200,
        token=admin,
    )
    r.call(
        "analytics: departments blocked for citizen -> 403",
        "GET",
        "/api/v1/analytics/departments",
        expect=403,
        token=citizen,
    )

    # -------------------------------------------------------------------- AI
    print("\n[ai]")
    r.call(
        "ai: analyze complaint",
        "POST",
        "/api/v1/ai/analyze-complaint",
        expect=200,
        token=citizen,
        json={
            "title": "Sewage overflowing onto the road near the school gate",
            "description": (
                "The main drain outside the primary school has been overflowing since "
                "yesterday. Children walk through the sewage to reach the gate and the "
                "smell is unbearable. Mosquitoes have increased sharply this week."
            ),
            "latitude": SPOT_A[0],
            "longitude": SPOT_A[1],
            "check_duplicates": True,
        },
    )
    r.call(
        "ai: analyze rejects short text -> 422",
        "POST",
        "/api/v1/ai/analyze-complaint",
        expect=422,
        token=citizen,
        json={"title": "Bad", "description": "short"},
    )
    r.call(
        "ai: briefing blocked for citizen -> 403",
        "GET",
        "/api/v1/ai/admin-briefing",
        expect=403,
        token=citizen,
    )
    r.call(
        "ai: admin briefing",
        "GET",
        "/api/v1/ai/admin-briefing",
        expect=200,
        token=admin,
        params={"window_hours": 24},
    )

    return r.summary()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    print(f"Bhopal CivicAI — endpoint smoke test against {args.base_url}")
    return run(args.base_url, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
