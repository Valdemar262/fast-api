import argparse
import asyncio
import sys

from pydantic import ValidationError

from app.core.security import hash_password
from app.db.seed import seed
from app.db.session import AsyncSessionLocal
from app.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas import UserCreate


async def create_admin(name: str, email: str, password: str) -> None:
    try:
        payload = UserCreate(name=name, email=email, password=password)
    except ValidationError as exc:
        print("Invalid input:", file=sys.stderr)
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            print(f" {field}: {error['msg']}", file=sys.stderr)
        raise SystemExit(1) from exc

    async with AsyncSessionLocal() as session:
        repository = UserRepository(session)

        existing_user = await repository.get_by_email(email)

        if existing_user is not None:
            existing_user.role = UserRole.ADMIN
            await session.commit()
            print(f"User {email} promoted to Admin")
            return

        user = await repository.create(
            **payload.model_dump(exclude={"password"}),
            password_hash=hash_password(payload.password),
            role=UserRole.ADMIN,
        )

        await session.commit()
        print(f"Admin created: {user.email} (id={user.id})")
        return


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    admin = sub.add_parser("create-admin")
    admin.add_argument("--name", type=str, required=True)
    admin.add_argument("--email", type=str, required=True)
    admin.add_argument("--password", type=str, required=True)

    seed_cmd = sub.add_parser("seed", help="Populate the database with development data")
    seed_cmd.add_argument(
        "--fresh",
        action="store_true",
        help="Truncate all tables and reset id sequences before seeding",
    )

    args = parser.parse_args()

    match args.command:
        case "create-admin":
            asyncio.run(create_admin(args.name, args.email, args.password))
        case "seed":
            asyncio.run(seed(fresh=args.fresh))


if __name__ == "__main__":
    main()
