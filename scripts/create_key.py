"""Create an API key directly against the local database (offline admin path).

Usage:  python scripts/create_key.py "jarvis-phone" tools,chat
"""
import sys

sys.path.insert(0, ".")
from app.core.config import settings  # noqa: E402
from app.services.key_service import KeyService  # noqa: E402


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "default"
    scopes = sys.argv[2].split(",") if len(sys.argv) > 2 else ["tools"]
    svc = KeyService(settings.database_path)
    created = svc.create_key(name, scopes)
    print(f"Key created (id {created['id']}) for {name}: {created['key']}")
    print("Store it now — only the hash is kept.")


if __name__ == "__main__":
    main()
