#!/usr/bin/env python
"""Mint a local HS256 access token that mimics a Supabase JWT.

**Development only.** This is for exercising Swagger and the smoke test without
a live Supabase project; it requires SUPABASE_JWT_SECRET to be set locally and
will refuse to run when APP_ENV=production. Real tokens come from Supabase Auth.

Usage:
    python scripts/dev_token.py --email citizen@example.com
    python scripts/dev_token.py --email admin@bhopalcivicai.in --name "City Admin"
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.config import settings


def mint(email: str, name: str | None, hours: int, user_id: str | None) -> str:
    if settings.is_production:
        raise SystemExit("Refusing to mint dev tokens with APP_ENV=production.")
    if not settings.supabase_jwt_secret:
        raise SystemExit(
            "SUPABASE_JWT_SECRET is not set. Add it to .env to mint local tokens."
        )

    now = datetime.now(UTC)
    # Supabase derives the user id from auth.users; deterministic per email here
    # so repeated runs map to the same profile row.
    subject = user_id or str(uuid.uuid5(uuid.NAMESPACE_URL, f"bhopal-civicai:{email}"))

    claims = {
        "sub": subject,
        "email": email,
        "aud": settings.supabase_jwt_audience,
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
        "session_id": str(uuid.uuid4()),
        "app_metadata": {"provider": "email", "providers": ["email"]},
        "user_metadata": {"full_name": name or email.split("@")[0].title()},
    }
    if settings.expected_issuer:
        claims["iss"] = settings.expected_issuer

    return jwt.encode(claims, settings.supabase_jwt_secret, algorithm="HS256")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="User email address.")
    parser.add_argument("--name", default=None, help="Display name.")
    parser.add_argument("--hours", type=int, default=12, help="Token lifetime.")
    parser.add_argument("--user-id", default=None, help="Explicit auth user UUID.")
    parser.add_argument(
        "--quiet", action="store_true", help="Print only the token (for piping)."
    )
    args = parser.parse_args()

    token = mint(args.email, args.name, args.hours, args.user_id)
    if args.quiet:
        print(token)
        return

    is_admin = args.email.lower() in settings.admin_email_list
    print(f"email : {args.email}")
    print(f"role  : {'admin (email is in ADMIN_EMAILS)' if is_admin else 'citizen'}")
    print(f"expiry: {args.hours}h")
    print("\nPaste this into Swagger's Authorize dialog:\n")
    print(token)
    print("\nOr use it with curl:\n")
    print(f'  curl -H "Authorization: Bearer {token}" \\')
    print("       http://localhost:8000/api/v1/auth/me")


if __name__ == "__main__":
    main()
