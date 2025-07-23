import json
import os
import hashlib
from datetime import datetime

STATS_FILE = "bot_stats.json"


def hash_id(id_value):
    return hashlib.sha256(str(id_value).encode()).hexdigest()


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {
            "unique_users": set(),
            "unique_chats": set(),
            "total_links": 0,
            "started_at": datetime.utcnow().isoformat() + "Z",
        }
    with open(STATS_FILE, "r") as f:
        data = json.load(f)
        # Convert lists to sets
        data["unique_users"] = set(data.get("unique_users", []))
        data["unique_chats"] = set(data.get("unique_chats", []))
        return data


def save_stats(stats):
    data_to_save = stats.copy()
    data_to_save["unique_users"] = list(stats["unique_users"])
    data_to_save["unique_chats"] = list(stats["unique_chats"])
    with open(STATS_FILE, "w") as f:
        json.dump(data_to_save, f, indent=2)


def print_stats():
    stats = load_stats()
    started_at_iso = stats.get("started_at", None)
    if started_at_iso:
        try:
            dt = datetime.fromisoformat(started_at_iso.replace("Z", "+00:00"))
            started_at = dt.strftime("%Y.%m.%d %H:%M")
        except Exception:
            started_at = started_at_iso
    else:
        started_at = "unknown"

    print("Current Bot Stats:")
    print(f"Bot started at (UTC): {started_at}")
    print(f"Unique users: {len(stats['unique_users'])}")
    print(f"Unique chats: {len(stats['unique_chats'])}")
    print(f"Total links processed: {stats['total_links']}")


if __name__ == "__main__":
    print_stats()
