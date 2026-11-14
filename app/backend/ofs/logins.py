"""The five demo logins (plan §6, Q10), one per role.

Run: `python -m ofs.logins --file <path>`. If the file exists, its passwords are reused, so a fresh database gets
the same logins back. If it doesn't, five passwords are generated straight into it (mode 0600). Either way only the
bcrypt hashes reach the database, and nothing is printed but the emails (the credentials rule: write into the file,
never echo).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
from pathlib import Path

from sqlalchemy import select

from .auth import hash_password
from .models import User
from .seed import DEMO_LOGINS


def _read(path: Path) -> dict[str, str]:
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
    return {k.strip(): v.strip() for k, v in pairs}


def _passwords(path: Path) -> dict[str, str]:
    """Reuse the file's passwords, or generate five straight into a new 0600 file."""
    if path.exists():
        return _read(path)
    passwords = {email: secrets.token_urlsafe(12) for email in DEMO_LOGINS.values()}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("".join(f"{email}={pw}\n" for email, pw in passwords.items()))
    return passwords


async def _store(passwords: dict[str, str]) -> None:
    from .db import SessionFactory, engine

    async with SessionFactory() as session:
        for email in DEMO_LOGINS.values():
            user = await session.scalar(select(User).where(User.email == email))
            if user is None:
                session.add(User(email=email, password_hash=hash_password(passwords[email])))
            else:
                user.password_hash, user.disabled = hash_password(passwords[email]), False
        await session.commit()
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--file", type=Path, required=True)
    asyncio.run(_store(_passwords(parser.parse_args().file)))
    print("logins set:", " ".join(DEMO_LOGINS.values()))


if __name__ == "__main__":
    main()
