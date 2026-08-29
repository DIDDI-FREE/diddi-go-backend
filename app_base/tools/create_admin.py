"""Create or update a local DiddiGo admin and optionally print an access token.

This tool is for DiddiGo local/staging operations when the app uses its local
`auth.users` table. In DiddiFreeID/JWKS mode, admin users and tokens must come
from DiddiFreeID.
"""

from __future__ import annotations

import argparse
import asyncio
import re
from uuid import UUID

from sqlalchemy import select

from app_base.core.database import async_session_factory, engine
from app_base.core.security import issue_access_token, issue_refresh_token
from app_base.modules.auth.infra.models import UserModel

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def _normalise_phone(phone: str) -> str:
    normalised = "".join(phone.split())
    if not _E164.match(normalised):
        raise SystemExit("phone must be E.164, for example +2250700000000")
    return normalised


async def upsert_admin(*, phone: str, full_name: str | None) -> UserModel:
    phone = _normalise_phone(phone)
    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).where(UserModel.phone == phone))
        user = result.scalar_one_or_none()
        if user is None:
            user = UserModel(phone=phone, full_name=full_name, role="admin", status="active")
            session.add(user)
            await session.flush()
        else:
            user.full_name = full_name or user.full_name
            user.role = "admin"
            user.status = "active"
            await session.flush()
        await session.commit()
        return user


async def run(args: argparse.Namespace) -> None:
    user = await upsert_admin(phone=args.phone, full_name=args.full_name)
    print(f"admin_user_id={user.id}")
    print(f"phone={user.phone}")
    print(f"role={user.role}")
    print(f"status={user.status}")
    if args.print_token:
        print(f"access_token={issue_access_token(UUID(str(user.id)), user.role)}")
    if args.print_refresh_token:
        print(f"refresh_token={issue_refresh_token(UUID(str(user.id)))}")
    await engine.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create/update a local DiddiGo admin user.")
    parser.add_argument("--phone", required=True, help="Admin phone in E.164 format, for example +2250700000000.")
    parser.add_argument("--full-name", default="DiddiGo Admin", help="Display name stored in local auth.users.")
    parser.add_argument("--print-token", action="store_true", help="Print a short-lived admin access token.")
    parser.add_argument("--print-refresh-token", action="store_true", help="Print a refresh token too.")
    return parser


def main() -> None:
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
