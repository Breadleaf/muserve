import os
import flask
import flask_cors
import multiprocessing.managers as mm
import datetime
import jwt
import functools
import typing
import urllib.parse as up

import psycopg2 as pg
import argon2 as a2
import argon2.low_level as a2ll

ISSUER = os.getenv("ISSUER", "http://localhost:7000")
AUDIENCE = os.getenv("AUDIENCE", "muserve-api") # use for both action & refresh
JWT_KEY = os.getenv("JWT_KEY", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACTION_TTL_MIN = int(os.getenv("ACTION_TTL_MIN", "10"))
SOCK_PATH = os.getenv("SOCK_PATH", "/sockets/refresh_state.sock")
AUTHKEY = os.getenv("AUTHKEY", "change-me").encode()
REFRESH_COOKIE = os.getenv("REFRESH_COOKIE", "rt")
DATABASE_URL = os.getenv("DATABASE_URL", "")

#
# argon2 password hasher
#

PASSWORD_HASHER = a2.PasswordHasher(
    time_cost=2, # iterations
    memory_cost=18750, # 18650 KiB -> 19.2 MB
    parallelism=1, # 1 parallel thread
    hash_len=32, # explicit default value
    salt_len=16, # explicit default value
    type=a2ll.Type.ID,
)

#
# State daemon client
#

class RefreshRecordDict(typing.Dict[str, typing.Any]):
    pass

class RefreshStoreProxy(typing.Protocol):
    def new_refresh(
        self,
        user_id: int,
        family_id: typing.Optional[str] = None,
        parent_jti: typing.Optional[str] = None,
    ) -> typing.Tuple[str, str, int]: ...

    def get_token(self, jti: str) -> typing.Optional[RefreshRecordDict]: ...

    def mark_revoked(self, jti: str) -> None: ...

    def revoke_family(self, family_id: str) -> None: ...

class RefreshStoreClient(mm.BaseManager):
    def store(self) -> RefreshStoreProxy: ...

RefreshStoreClient.register("store")

def connect_refresh_store() -> RefreshStoreProxy:
    manager = RefreshStoreClient(address=SOCK_PATH, authkey=AUTHKEY)
    manager.connect()
    return typing.cast(RefreshStoreProxy, manager.store())

# initialized in create_server()
STORE: RefreshStoreProxy
DATABASE: pg.extensions.connection

#
# JWT helpers
#

def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc)

def mint_action_token(user_id):
    issued_at = _now_utc()
    expires_at = issued_at + datetime.timedelta(minutes=ACTION_TTL_MIN)
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": str(user_id),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": os.urandom(8).hex(),
        "typ": "action",
    }
    return jwt.encode(payload, JWT_KEY, algorithm=JWT_ALG)

def verify_action_token(token):
    return jwt.decode(
        token,
        JWT_KEY,
        algorithms=[JWT_ALG],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={
            "require": [
                "exp",
                "sub",
                "jti",
            ]
        },
    )

def verify_refresh_token(token):
    return jwt.decode(
        token,
        JWT_KEY,
        algorithms=[JWT_ALG],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={
            "require": [
                "exp",
                "sub",
                "jti",
            ]
        },
    )

# decorator to protect endpoints with JWT
def require_action(handler):
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        auth_header = flask.request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"error": "missing bearer token"}, 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = verify_action_token(token)

        except jwt.PyJWTError as err:
            return {"error": "invalid action token", "detail": str(err)}, 401

        flask.g.user_id = int(payload["sub"])
        return handler(*args, **kwargs)

    return wrapper

#
# flask app
#

def create_server():
    server = flask.Flask(__name__)
    flask_cors.CORS(
        server,
        resources={r"/*": {"origins": ["http://localhost:8000"]}},
        supports_credentials=True,
    )

    # this is safe because docker compose will wait for auth_state healthy
    global STORE
    STORE = connect_refresh_store()

    def db_connect():
        global DATABASE

        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is required in auth service")

        parsed = up.urlparse(DATABASE_URL)

        DATABASE = pg.connect(
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port,
        )

        DATABASE.autocommit = True

    db_connect()

    # simple health check for docker
    @server.route("/health")
    def health():
        print("/health: ping~!", flush=True)
        return "Ok"

    @server.post("/introspect")
    def introspect():
        auth_header = flask.request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        else:
            body = flask.request.get_json(silent=True) or {}
            token = body.get("token")

        if not token:
            return {"active": False, "error": "missing token"}, 400

        try:
            payload = verify_action_token(token)
            return {
                "active": True,
                "sub": payload["sub"],
                "user_id": int(payload["sub"]),
                "exp": payload["exp"],
                "jti": payload["jti"],
            }
        except jwt.PyJWTError as e:
            return {"active": False, "error": str(e)}, 401

    @server.post("/login")
    def login():
        body = flask.request.get_json(silent=True) or {}
        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""
        if not email or not password:
            return {"error": "email and password required"}, 400

        cur = DATABASE.cursor()
        cur.execute(
            """
            SELECT id, password_hash FROM users
            WHERE LOWER(email)=LOWER(%s)
            LIMIT 1;
            """,
            (email,)
        )
        row = cur.fetchone()
        if not row:
            return {"error": "invalid credentials"}, 401

        user_id, password_hash = row

        try:
            PASSWORD_HASHER.verify(password_hash, password)
        except Exception:
            return {"error": "invalid credentials"}, 401

        # issue first refresh token in a new family
        token_id, family_id, refresh_expiry = STORE.new_refresh(user_id)

        refresh_payload = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": str(user_id),
            "jti": token_id,
            "fid": family_id,
            "typ": "refresh",
            "exp": refresh_expiry,
        }

        refresh_jwt = jwt.encode(refresh_payload, JWT_KEY, algorithm=JWT_ALG)

        resp = flask.make_response({
            "action_token": mint_action_token(user_id),
            "expires_in": ACTION_TTL_MIN * 60,
        })

        resp.set_cookie(
            REFRESH_COOKIE,
            refresh_jwt,
            httponly=True,
            secure=True,
            samesite="Strict",
            path="/refresh",
        )

        return resp

    @server.post("/register")
    def register():
        body = flask.request.get_json(silent=True) or {}
        name = (body.get("name") or "").strip()
        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""
        if not name or not email or not password:
            return {"error": "name, email, and password are required"}, 400

        # hash the password
        try:
            hashed_password = PASSWORD_HASHER.hash(password)
        except Exception as ex:
            return {"error": "failed to hash password"}, 500

        cur = DATABASE.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (name, email, is_admin, password_hash)
                VALUES (%s, %s, FALSE, %s)
                RETURNING id;
                """,
                (name, email, hashed_password),
            )
            row = cur.fetchone()
            if not row  or not row[0]:
                return {"error": "could not fetch user_id after insert"}, 500
            user_id = row[0]
        except pg.Error as e:
            # unique violation on email etc
            return {"error": "could not create user", "detail": str(e)}, 201

        return {"id": user_id, "email": email}, 201

    @server.post("/logout")
    def logout():
        # revoke current refresh token (device sign-out)
        refresh_cookie = flask.request.cookies.get(REFRESH_COOKIE) or ""
        if not refresh_cookie:
            return {"status": "ok"} # already logged out

        try:
            payload = verify_refresh_token(refresh_cookie)
        except jwt.PyJWTError:
            return {"status": "ok"}

        STORE.mark_revoked(payload.get("jti"))
        resp = flask.make_response({"status": "ok"})
        resp.set_cookie(
            REFRESH_COOKIE,
            "",
            path="/refresh",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0,
        )
        return resp

    @server.post("/logout_all")
    def logout_all():
        # logout whole family (all devices)
        refresh_cookie = flask.request.cookies.get(REFRESH_COOKIE) or ""
        if refresh_cookie:
            try:
                payload = verify_refresh_token(refresh_cookie)
                family_id = payload.get("fid")
                if family_id:
                        STORE.revoke_family(family_id)
            except jwt.PyJWTError:
                pass
        resp = flask.make_response({"status": "ok"})
        resp.set_cookie(
            REFRESH_COOKIE,
            "",
            path="/refresh",
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=0,
        )
        return resp

    @server.post("/refresh")
    def refresh():
        """
        rotate the refresh token and return a new action token
        """
        refresh_cookie = flask.request.cookies.get(REFRESH_COOKIE) or ""
        if not refresh_cookie:
            return {"error": "missing refresh cookie"}, 401

        try:
            payload = verify_refresh_token(refresh_cookie)
            if payload.get("typ") != "refresh":
                raise jwt.InvalidTokenError("wrong type")
        except jwt.PyJWTError as err:
            return {"error": "invalid refresh", "detail": str(err)}, 401

        # look up server-side record by jti
        refresh_record = STORE.get_token(payload["jti"])
        now_ts = int(_now_utc().timestamp())

        # missing or expired or revoked: revoke family
        if (not refresh_record) or \
            refresh_record["revoked"] or \
            (refresh_record["expires_at"] <= now_ts):
            STORE.revoke_family(payload.get("fid"))
            return {"error": "refresh invalid; family revoked"}, 401

        # valid: rotate refresh
        STORE.mark_revoked(payload["jti"])
        new_token_id, family_id, refresh_expiry = STORE.new_refresh(
            int(payload["sub"]),
            family_id=payload["fid"],
            parent_jti=payload["jti"],
        )

        new_refresh_payload = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": payload["sub"],
            "jti": new_token_id,
            "fid": family_id,
            "typ": "refresh",
            "exp": refresh_expiry,
        }
        new_refresh_jwt = jwt.encode(
            new_refresh_payload,
            JWT_KEY,
            algorithm=JWT_ALG
        )

        resp = flask.make_response({
            "action_token": mint_action_token(int(payload["sub"])),
            "expires_in": ACTION_TTL_MIN * 60,
        })
        resp.set_cookie(
            REFRESH_COOKIE,
            new_refresh_jwt,
            httponly=True,
            secure=True,
            samesite="Strict",
            path="/refresh",
        )

        return resp

    # example of a protected endpoint using the action tokens
    @server.get("/me")
    @require_action
    def me():
        return {"user_id": flask.g.user_id}

    return server

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=7000,
        use_reloader=False
    )
