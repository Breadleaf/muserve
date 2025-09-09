import threading
import json
import os
import heapq
import uuid
import time
import datetime
import multiprocessing.managers as mm
import atexit

# https://en.wikipedia.org/wiki/JSON_Web_Token

SOCK_PATH = os.getenv("SOCK_PATH", "/sockets/refresh_state.sock")
STATE_PATH = os.getenv("STATE_PATH", "/state/refresh_state.json")
REFRESH_TTL_DAYS = int(os.getenv("REFRESH_TTL_DAYS", 14))
AUTHKEY = os.getenv("AUTHKEY", "change-me").encode()

_generate_uuid = lambda: uuid.uuid4().hex
_get_time_seconds = lambda: int(time.time())

class RefreshStore:
    def __init__(self):
        self.tokens = {}
        self.family = {}
        self.exp_heap = []
        self.lock = threading.RLock()
        self._load()

    #
    # persistence
    #

    def _load(self):
        # if no state exists, exit early
        if not os.path.exists(STATE_PATH):
            return

        # load state json object
        with open(STATE_PATH) as state_file:
            obj = json.load(state_file)

        # restore from state object
        self.tokens = obj.get("tokens", {})
        self.family = {
            key: set(value)
            for key, value in
            obj.get("family", {}).items()
        }
        self.exp_heap = [
            tuple(elem)
            for elem in
            obj.get("exp_heap", [])
        ]
        # transform exp_heap from list to heap
        # https://docs.python.org/3/library/heapq.html
        heapq.heapify(self.exp_heap)

    def _save(self):
        # make the dir regardless of if it exists or not
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)

        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w") as outfile:
            # write to a temporary file
            json.dump(
                {
                    "tokens": self.tokens,
                    "family": {
                        key: list(value)
                        for key, value in
                        self.family.items()
                    },
                    "exp_heap": self.exp_heap,
                },
                outfile
            )
            # convert temp file to final file
            os.replace(tmp, STATE_PATH)

    def shutdown(self):
        with self.lock:
            self._save()

    #
    # API
    #

    def new_refresh(self, user_id: int, family_id=None, parent_jti=None):
        with self.lock:
            jti = _generate_uuid()
            expire = int(
                (
                    datetime.datetime.now(datetime.timezone.utc) +
                    datetime.timedelta(days=REFRESH_TTL_DAYS)
                ).timestamp()
            )
            fam_id = family_id or _generate_uuid()
            record = {
                "user_id": user_id,
                "family_id": fam_id,
                "expires_at": expire,
                "revoked": False,
                "parent_jti": parent_jti,
            }
            self.tokens[jti] = record
            self.family.setdefault(fam_id, set()).add(jti)
            heapq.heappush(self.exp_heap, (expire, jti))
            return jti, fam_id, expire

    def get_token(self, jti: str):
        with self.lock:
            return self.tokens.get(jti)

    def mark_revoked(self, jti: str):
        with self.lock:
            record = self.tokens.get(jti)

            # if the record doesn't exist exit early
            if not record:
                return

            # revoke token
            record["revoked"] = True
            fam_id = record["family_id"]

            family_jtis = self.family.get(fam_id)
            if family_jtis is not None:
                family_jtis.discard(jti) # NOTE: .discard() avoids KeyError

                # if the set is empty, there are no active tokens left
                if not family_jtis:
                    self.family.pop(fam_id, None)


    def revoke_family(self, family_id):
        with self.lock:
            for fam in list(self.family.get(family_id, set())):
                self.mark_revoked(fam)

    def garbage_collect(self):
        with self.lock:
            now = _get_time_seconds()

            # expire old tokens
            while self.exp_heap and self.exp_heap[0][0] <= now:
                _, j = heapq.heappop(self.exp_heap)
                record = self.tokens.get(j)
                if record and record["expires_at"] <= now:
                    self.mark_revoked(j)

            # persist after change
            self._save()

class StoreManager(mm.BaseManager):
    pass

STORE = RefreshStore()

StoreManager.register(
    "store",
    callable=lambda: STORE,
    exposed=(
        "new_refresh",
        "get_token",
        "mark_revoked",
        "revoke_family",
        "garbage_collect",
    ),
)

def main():
    # ensure socket dir exists
    os.makedirs(os.path.dirname(SOCK_PATH), exist_ok=True)

    # remove stale socket
    try:
        if os.path.exists(SOCK_PATH):
            os.unlink(SOCK_PATH)
    except FileNotFoundError:
        pass

    manager = StoreManager(address=SOCK_PATH, authkey=AUTHKEY)
    server = manager.get_server()

    # background garbage collect + autosave
    def background_thread():
        while True:
            time.sleep(10)
            try:
                STORE.garbage_collect()
            except Exception:
                pass

    # create thread
    threading.Thread(target=background_thread, daemon=True).start()

    atexit.register(STORE.shutdown)

    server.serve_forever()

if __name__ == "__main__":
    main()
