#!/usr/bin/env python
"""Grant the admin role — the operator-side path that bypasses signup.

Admins can never be created through the public API. Use this after the person
has signed up in Supabase (preferred), or pre-seed the role by email so it is
applied automatically on their first login.

Usage:
    # Promote an existing profile
    python scripts/create_admin.py --email official@bhopal.gov.in

    # Pre-seed before the person has ever signed in
    python scripts/create_admin.py --email official@bhopal.gov.in --pre-seed

    # Attach the admin to a department
    python scripts/create_admin.py --email pwd.head@bhopal.gov.in --department PWD

    # List current admins
    python scripts/create_admin.py --list
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database.init_db import create_tables
from app.database.session import SessionLocal
from app.models import Department, Profile, UserRole
from app.utils.config import settings


def list_admins() -> None:
    with SessionLocal() as db:
        admins = db.scalars(
            select(Profile).where(Profile.role == UserRole.ADMIN).order_by(Profile.email)
        ).all()
        if not admins:
            print("No admins exist yet.")
            return
        print(f"{len(admins)} admin(s):")
        for admin in admins:
            department = admin.department.code if admin.department else "-"
            active = "active" if admin.is_active else "disabled"
            print(f"  {admin.email:40} dept={department:10} {active}")


def promote(email: str, department_code: str | None, pre_seed: bool) -> int:
    email = email.strip().lower()
    with SessionLocal() as db:
        department = None
        if department_code:
            department = db.scalar(
                select(Department).where(Department.code == department_code.upper())
            )
            if department is None:
                print(f"error: no department with code {department_code!r}", file=sys.stderr)
                return 2

        profile = db.scalar(select(Profile).where(Profile.email == email))

        if profile is None:
            if not pre_seed:
                print(
                    f"error: no profile for {email!r}.\n"
                    "  The user must sign in once (which creates their profile), or\n"
                    "  re-run with --pre-seed to reserve the admin role for that email.",
                    file=sys.stderr,
                )
                return 1
            # Placeholder id; adopted and re-keyed on the user's first real login.
            profile = Profile(
                id=uuid.uuid4(),
                email=email,
                role=UserRole.ADMIN,
                city=settings.city_name,
                department_id=department.id if department else None,
            )
            db.add(profile)
            db.commit()
            print(
                f"pre-seeded admin role for {email}. It is applied automatically "
                "the first time they sign in with Supabase."
            )
            return 0

        was = profile.role.value
        profile.role = UserRole.ADMIN
        profile.is_active = True
        if department is not None:
            profile.department_id = department.id
        db.commit()
        print(
            f"{email}: {was} -> admin"
            + (f" (department {department.code})" if department else "")
        )
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Email address to promote.")
    parser.add_argument("--department", help="Department code, e.g. PWD.")
    parser.add_argument(
        "--pre-seed",
        action="store_true",
        help="Reserve the admin role for an email that has not signed up yet.",
    )
    parser.add_argument("--list", action="store_true", help="List current admins.")
    args = parser.parse_args()

    create_tables()  # no-op when the schema already exists

    if args.list:
        list_admins()
        return 0
    if not args.email:
        parser.error("--email is required (or use --list)")
    return promote(args.email, args.department, args.pre_seed)


if __name__ == "__main__":
    raise SystemExit(main())
