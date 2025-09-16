import flask

import StorageHandler

import datetime
import re
import os

CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", 64 * 1024))

def create_server():
    server = flask.Flask(__name__)

    CLIENT = StorageHandler.create_minio_client()

    store_bp = flask.Blueprint("store", __name__)

    @store_bp.route("/health")
    def health():
        print("/health: ping~!", flush=True)
        return "Ok"

    @store_bp.get("/stream")
    def stream():
        bucket = flask.request.args.get("bucket", "muserve")
        key = flask.request.args.get("key")
        if not key:
            return flask.jsonify({"error": "missing 'key'"}), 400

        # try to stat the object to get size, type, etc
        try:
            stat = CLIENT.stat_object(bucket, key)
        except Exception as e:
            return flask.jsonify({"error": "object not found", "detail": str(e)}), 404

        size = getattr(stat, "size", None)
        # TODO: consider using magic here
        ctype = stat.content_type or "application/octet-stream"
        etag = getattr(stat, "etag", None)
        lm = getattr(stat, "last_modified", None)
        if isinstance(lm, datetime.datetime) and lm.tzinfo is None:
            lm = lm.replace(tzinfo=datetime.timezone.utc)
        last_modified_header = lm.strftime("%a, %d %b %Y %H:%M:%S GMT") if lm else None

        # if size is unknown, ignore range and stream whole object (seek is disabled)
        range_header = flask.request.headers.get("Range")
        if size is None or not range_header:
            try:
                obj = CLIENT.get_object(bucket, key) # full object
            except Exception as e:
                return flask.jsonify({"error": "fetch failed", "detail": str(e)}), 502

            def gen():
                try:
                    for chunk in obj.stream(CHUNK_SIZE):
                        yield chunk
                finally:
                    obj.close()
                    obj.release_conn()

            headers = {
                "Content-Type": ctype,
                "Accept-Ranges": "none" if size is None else "bytes",
            }

            # only include Content-Length if it is known
            if size is not None:
                headers["Content-Length"] = str(size)
            if etag:
                headers["ETag"] = etag
            if last_modified_header:
                headers["Last-Modified"] = last_modified_header
            # support HEAD
            if flask.request.method == "HEAD":
                return flask.Response(status=200, headers=headers)
            return flask.Response(gen(), status=200, headers=headers)

        # parse single range header: "bytes=<start>-<end>" | "bytes=<start>" | "bytes=-<len>"
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match:
            cr_total = f"bytes */{size}"
            return flask.Response(status=416, headers={
                "Content-Range": cr_total,
                "Accept-Ranges": "bytes",
            })

        start_s, end_s, = match.groups()
        offset = 0
        length = None
        status = 206

        try:
            if start_s and end_s:
                # bytes=start-end
                start = int(start_s)
                end = int(end_s)
                if start > end or start >= size:
                    raise ValueError("invalid range")
                end = min(end, size - 1)
                offset = start
                length = end - start + 1
            elif start_s and not end_s:
                # bytes=start-
                start = int(start_s)
                if start >= size:
                    raise ValueError("invalid range")
                offset = start
                length = None # to EOF
            elif not start_s and end_s:
                # bytes=-len
                suf = int(end_s)
                if suf <= 0:
                    raise ValueError("invalid suffix")
                if suf >= size:
                    offset = 0
                    length = size
                else:
                    offset = size - suf
                    length = suf
            else:
                # bytes=-
                raise ValueError("empty range")

        except Exception as e:
            cr_total = f"bytes */{size}"
            return flask.Response(
                status=416,
                headers={
                    "Content-Range": cr_total,
                    "Accept-Ranges": "bytes",
                },
            )

        # fetch object portion
        try:
            obj = CLIENT.get_object(bucket, key, offset=offset, length=length)
        except Exception as e:
            return flask.jsonify({"error": "fetch failed", "detail": str(e)}), 502

        # build headers
        if length is None:
            content_length = size - offset
            end_byte = size - 1
        else:
            content_length = length
            end_byte = offset + length - 1

        headers = {
            "Content-Type": ctype,
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {offset}-{end_byte}/{size}",
        }

        if etag:
            headers["ETag"] = etag
        if last_modified_header:
            headers["Last-Modified"] = last_modified_header
        # support HEAD for range requests
        if flask.request.method == "HEAD":
            return flask.Response(status=status, headers=headers)

        # stream body
        def gen():
            try:
                for chunk in obj.stream(CHUNK_SIZE):
                    yield chunk
            finally:
                obj.close()
                obj.release_conn()

        return flask.Response(gen(), status=status, headers=headers)

    server.register_blueprint(store_bp, url_prefix="/store")

    return server

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )
