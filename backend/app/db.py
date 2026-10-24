import json
import sqlite3
import threading
from datetime import UTC, datetime

from . import config, machine

# ponytail: one global lock around state changes and hardware calls; per-bay locks if we ever run many bays
lock = threading.RLock()
conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

_active = "state NOT IN ({})".format(", ".join(f"'{s}'" for s in machine.TERMINAL))

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS drivers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  plate TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bays (
  id TEXT PRIMARY KEY,
  lock_id TEXT NOT NULL UNIQUE,
  ge_id INTEGER,
  name TEXT NOT NULL,
  out_of_service INTEGER NOT NULL DEFAULT 0,
  occupied INTEGER NOT NULL DEFAULT 0,
  last_seen_at TEXT
);
CREATE TABLE IF NOT EXISTS reservations (
  id TEXT PRIMARY KEY,
  bay_id TEXT NOT NULL REFERENCES bays,
  driver_id TEXT NOT NULL REFERENCES drivers,
  plate TEXT NOT NULL,
  state TEXT NOT NULL,
  previous_state TEXT,
  blocked_reason TEXT,
  fault_reason TEXT,
  grace_deadline TEXT,
  reminder_at TEXT,
  mismatch_deadline TEXT,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (driver_id, idempotency_key)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_bay ON reservations(bay_id) WHERE {_active};
CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_driver ON reservations(driver_id) WHERE {_active};
CREATE TABLE IF NOT EXISTS event_log (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  reservation_id TEXT,
  bay_id TEXT,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL
);
"""

# Demo drivers until the login decision (#5)
DRIVERS = [("d1", "Demo Driver 1", "M-AB 1234"), ("d2", "Demo Driver 2", "B-CD 5678")]


def now():
    return datetime.now(UTC)


def iso(dt):
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse(ts):
    return datetime.fromisoformat(ts) if ts else None


def init():
    with conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT OR IGNORE INTO drivers VALUES (?, ?, ?)", DRIVERS)
        conn.executemany(
            "INSERT OR IGNORE INTO bays (id, lock_id, name) VALUES (?, ?, ?)",
            [(f"bay-{i}", lock_id, f"Test bay {i}") for i, lock_id in enumerate(config.LOCK_IDS, 1)],
        )


def reset():
    with lock, conn:
        conn.executescript("DROP TABLE IF EXISTS reservations; DROP TABLE IF EXISTS event_log; DROP TABLE IF EXISTS bays; DROP TABLE IF EXISTS drivers;")
    init()


def one(sql, *args):
    return conn.execute(sql, args).fetchone()


def rows(sql, *args):
    return conn.execute(sql, args).fetchall()


def execute(sql, *args):
    with conn:
        conn.execute(sql, args)


def update(table, id, **fields):
    if table == "reservations":
        fields["updated_at"] = iso(now())
    sets = ", ".join(f"{k} = ?" for k in fields)
    execute(f"UPDATE {table} SET {sets} WHERE id = ?", *fields.values(), id)


def active_reservation(column, value):
    return one(f"SELECT * FROM reservations WHERE {column} = ? AND {_active}", value)


def log(kind, reservation_id=None, bay_id=None, **payload):
    execute(
        "INSERT INTO event_log (ts, reservation_id, bay_id, kind, payload) VALUES (?, ?, ?, ?, ?)",
        iso(now()), reservation_id, bay_id, kind, json.dumps(payload, ensure_ascii=False),
    )
