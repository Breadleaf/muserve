import minio

import os
import sys

MINIO_URL = os.environ.get("MINIO_URL", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")

def _create_minio_client():
    if not (MINIO_URL and MINIO_ACCESS_KEY and MINIO_SECRET_KEY):
        print(
            "[StorageHandler] error: need to define MINIO_URL, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    return minio.Minio(
        endpoint=MINIO_URL,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
    )

CLIENT = _create_minio_client()
