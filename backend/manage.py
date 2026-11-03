"""Explicit operator commands. Never creates default passwords or credits."""

import argparse
import getpass
import json
import uuid
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.orm import Session as DBSession
from database import configured_url, engine_for
from models import User, Restaurant, Dish, Session, utcnow
from auth import hash_password
from schemas import Signup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    user = sub.add_parser("create-user")
    user.add_argument("--email", required=True)
    user.add_argument("--name", required=True)
    user.add_argument("--role", choices=["customer", "restaurant", "admin"], default="customer")
    user.add_argument("--kitchen", help="Attach a restaurant owner to an unowned seeded kitchen ID")
    sub.add_parser("seed-catalog")
    sub.add_parser("cleanup-sessions")
    args = parser.parse_args()
    with DBSession(engine_for(configured_url())) as db, db.begin():
        if args.command == "create-user":
            password = getpass.getpass("Password (10+ characters): ")
            if password != getpass.getpass("Confirm password: "):
                raise SystemExit("Passwords do not match.")
            validated = Signup(email=args.email, name=args.name, password=password)
            if db.scalar(select(User).where(User.email == validated.email)):
                raise SystemExit("Email already exists.")
            account = User(
                id=uuid.uuid4().hex,
                email=validated.email,
                name=validated.name,
                password_hash=hash_password(password),
                role=args.role,
                balance=0,
            )
            db.add(account)
            db.flush()
            if args.role == "restaurant":
                if args.kitchen:
                    kitchen = db.scalar(
                        select(Restaurant).where(Restaurant.id == args.kitchen).with_for_update()
                    )
                    if not kitchen or kitchen.owner_id:
                        raise SystemExit("Kitchen is missing or already owned.")
                    kitchen.owner_id = account.id
                else:
                    db.add(
                        Restaurant(
                            id=uuid.uuid4().hex, owner_id=account.id, name=account.name + " Kitchen"
                        )
                    )
            elif args.kitchen:
                raise SystemExit("--kitchen requires restaurant role.")
            print("Created account. No wallet credit was added.")
        elif args.command == "seed-catalog":
            catalog = json.loads(
                Path(__file__).with_name("catalog.json").read_text(encoding="utf-8")
            )
            for row in catalog["restaurants"]:
                if not db.get(Restaurant, row["id"]):
                    data = {
                        {"nameAr": "name_ar", "descriptionAr": "description_ar"}.get(k, k): v
                        for k, v in row.items()
                    }
                    db.add(Restaurant(**data))
            db.flush()
            for row in catalog["dishes"]:
                if not db.get(Dish, row["id"]):
                    data = {
                        {
                            "restaurantId": "restaurant_id",
                            "nameAr": "name_ar",
                            "descriptionAr": "description_ar",
                        }.get(k, k): v
                        for k, v in row.items()
                    }
                    db.add(Dish(**data))
            print(
                "Fictional catalog seeded. Existing records preserved; no accounts or credit created."
            )
        else:
            db.execute(delete(Session).where(Session.expires_at < utcnow()))
            # Rate buckets use variable window sizes; removing old rows requires age metadata.
            print("Expired sessions removed.")


if __name__ == "__main__":
    main()
