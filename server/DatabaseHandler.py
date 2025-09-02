import psycopg2

import os
import sys
import urllib.parse as up

class DatabaseHandler:
    # def __init__(self, db_url):
    def __init__(self):
        db_url = os.environ.get("DATABASE_URL", None)
        if not db_url:
            print(f"envvar DATABASE_URL doesn't exist", file=sys.stderr)
            sys.exit(1)

        parsed_url = up.urlparse(db_url)

        try:
            self.con = psycopg2.connect(
                database=parsed_url.path[1:],
                user=parsed_url.username,
                password=parsed_url.password,
                host=parsed_url.hostname,
                port=parsed_url.port
            )

        except psycopg2.Error as e:
            print(
                f"error connecting to PostgreSQL server: {e}",
                file=sys.stderr
            )
            sys.exit(1)

    def fetch(self, query, values=()):
        try:
            cur = self.con.cursor()
            cur.execute(query, values)
            res = cur.fetchall()

            # return (True, result) for golang-like error handling
            return (True, res)
        
        except psycopg2.Error as e:
            # return (False, error) for golang-like error handling
            return (False, f"db error from fetch(): {e}")

    def insert(self, query, values=()):
        try:
            cur = self.con.cursor()
            cur.execute(query, values)
            self.con.commit()
            cur.close()

            # return no error
            return None

        except psycopg2.Error as e:
            return f"db error from insert(): {e}"
