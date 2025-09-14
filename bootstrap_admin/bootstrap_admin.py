import os
import urllib.parse as up
import sys

import psycopg2 as pg
import argon2 as a2
import argon2.low_level as a2ll

ADMIN_NAME = os.environ.get("BOOTSTRAP_ADMIN_NAME", "admin")
ADMIN_EMAIL = (os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin") or "").strip().lower()
ADMIN_PASSWORD = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "admin")

PASSWORD_HASHER = a2.PasswordHasher(
    time_cost=2, # iterations
    memory_cost=18750, # 18650 KiB -> 19.2 MB
    parallelism=1, # 1 parallel thread
    hash_len=32, # explicit default value
    salt_len=16, # explicit default value
    type=a2ll.Type.ID,
)

DATABASE_URL = os.environ.get("DATABASE_URL", None)

def _database_connect() -> pg.extensions.connection:
    if not DATABASE_URL:
        print(
            "[bootstrap] error: DATABASE_URL is not defined",
            file=sys.stderr,
            flush=True
        )
        sys.exit(1)

    parsed = up.urlparse(DATABASE_URL)
    conn = pg.connect(
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port,
    )
    conn.autocommit = True
    return conn

DATABASE = _database_connect()

if __name__ == "__main__":
    cur = DATABASE.cursor()

    # if admin level users exist, return early
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE;")
    row = cur.fetchone()
    if not row:
        print(
            "[bootstrap] error: failed to fetch admin count",
            file=sys.stderr,
            flush=True
        )
        sys.exit(1)

    count = row[0]
    if count > 0:
        print("[bootstrap] admin exists; skipping", flush=True)
        sys.exit(0)

    # hash the bootstrap admin user's password then insert user into database
    hashed = PASSWORD_HASHER.hash(ADMIN_PASSWORD)
    cur.execute(
        """
        INSERT INTO users (name, email, is_admin, password_hash)
        VALUES (%s, %s, TRUE, %s)
        ON CONFLICT (email) DO UPDATE
            SET is_admin = EXCLUDED.is_admin, password_hash = EXCLUDED.password_hash
        RETURNING id;
        """,
        (ADMIN_NAME, ADMIN_EMAIL, hashed),
    )

    # get the uuid for the admin user and log it
    row = cur.fetchone()
    if not row:
        print(
            "[bootstrap] error: failed to fetch return id after admin creation/update",
            file=sys.stderr,
            flush=True
        )
        sys.exit(1)

    print(f"[bootstrap] admin id={row[0]} email={ADMIN_EMAIL}", flush=True)
