import psycopg2

import os
import sys
import urllib.parse as up

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL", None)
    result = up.urlparse(db_url)

    try:
        con = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )

    except psycopg2.Error as e:
        print(f"error connecting to postgres: {e}", file=sys.stderr)
        sys.exit(1)

    cur = con.cursor()

    try:
        with open("./queries/add_user.sql", "r") as f:
            query = f.read()
    except Exception as ex:
        print(f"error opening file: {ex}", file=sys.stderr)
        sys.exit(1)

    try:
        cur.execute(
            query,
            ('test', 'test@not_real.com', True)
        )
    except psycopg2.Error as e:
        print(f"error executing query: {e}")
        con.rollback()
        sys.exit(1)

    print(cur.query)

    con.commit() # make it happen

    cur.close()
    con.close()
