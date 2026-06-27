"""Seed admin and super_admin users into the database/users.json."""

import json
import uuid
import bcrypt
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


ADMIN_USERS = [
    {
        "username": "admin",
        "email": "admin@codecoach.ai",
        "password": "admin123",
        "role": "admin",
    },
    {
        "username": "superadmin",
        "email": "superadmin@codecoach.ai",
        "password": "superadmin123",
        "role": "super_admin",
    },
]


def seed():
    if not USERS_FILE.exists():
        users = []
    else:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)

    existing_usernames = {u["username"] for u in users}
    now = datetime.now(timezone.utc).isoformat()

    for au in ADMIN_USERS:
        if au["username"] in existing_usernames:
            # Update role if user already exists
            for u in users:
                if u["username"] == au["username"]:
                    u["role"] = au["role"]
                    print(f"  Updated role for '{au['username']}' to '{au['role']}'")
                    break
        else:
            users.append(
                {
                    "id": str(uuid.uuid4()),
                    "username": au["username"],
                    "email": au["email"],
                    "hashed_password": hash_password(au["password"]),
                    "created_at": now,
                    "is_active": True,
                    "oauth_provider": None,
                    "oauth_id": None,
                    "role": au["role"],
                }
            )
            print(f"  Created user '{au['username']}' with role '{au['role']}'")
        existing_usernames.add(au["username"])

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

    print(f"\nDone. Users file: {USERS_FILE}")


if __name__ == "__main__":
    seed()
