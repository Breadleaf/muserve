import minio

import os
import sys

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("1","true","yes")

def create_minio_client():
    if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY):
        print(
            "[StorageHandler] error: need to define MINIO_URL, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    return minio.Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )
