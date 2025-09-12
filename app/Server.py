import flask
import requests

import functools
import tempfile
import threading
import os

import DatabaseHandler
import MusicHandler

AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://auth:7000")

def require_action(handler):
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        auth_header = flask.request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"error": "missing bearer token"}, 401

        try:
            req = requests.post(
                f"{AUTH_BASE_URL}/introspect",
                headers={"Authorization": auth_header},
                timeout=3,
            )
        except requests.RequestException as e:
            return {"error": "auth service unavailable", "detail": str(e)}, 503

        if req.status_code != 200 or not req.json().get("activate"):
            return {"error": "invalid token"}, 401

        flask.g.user_id = int(req.json()["user_id"])
        return handler(*args, **kwargs)

    return wrapper

def create_server():
    server = flask.Flask(__name__)

    db_handler = DatabaseHandler.DatabaseHandler()
    music_handler = MusicHandler.MusicHandler(["audio/mpeg"])

    @server.route("/upload")
    def upload():
        return flask.render_template("upload.html")

    @server.route("/send", methods=["POST"])
    @require_action
    def send():
        uploaded_files = list(flask.request.files.values())

        if not uploaded_files:
            return flask.jsonify({"error": "no files uploaded"}), 400

        def ingest_file(file, outputs, idx):
            try:
                with tempfile.TemporaryDirectory() as tempdir:
                    # reset file pointer just in case not perfect
                    file.seek(0)

                    out = []

                    # TODO: defer this action to the user during upload, some songs may break if their
                    #       title has a file extension for stylistic choice.
                    # get the filename without extension(s)
                    """
                    real_filename = file.filename
                    ext = " "
                    while ext:
                        (real_filename, ext) = os.path.splitext(real_filename)
                    """
                    # if a user has something like a.b.c assume a.b is a stylistic choice from the artist
                    (real_filename, _) = os.path.splitext(file.filename)

                    # save to temp dir
                    safe_name = werkzeug.utils.secure_filename(real_filename or f"upload_{idx}")
                    save_path = f"{tempdir}/{safe_name}"
                    file.save(save_path)

                    out.append(f"ingest file: {save_path}, filename: {real_filename}")

                    # ingest the file
                    file_buffers, _, err = music_handler.convert_file(save_path, safe_name)
                    if file_buffers:
                        out.append(f"buffers: {file_buffers}")
                    else:
                        out.append(f"error converting files: {err}")

                    outputs[idx] = "\n".join(out)
            except Exception as e:
                outputs[idx] = f"error converting files: {e}"

        threads = []
        outputs = ["" for _ in uploaded_files]

        for idx, file in enumerate(uploaded_files):
            if (not file) or (not file.filename):
                outputs[idx] = "skipped: empty filename"

            # check if file is valid
            file_contents = file.read()

            valid_file_type = music_handler.validate_file(file_contents)
            if not valid_file_type:
                outputs[idx] = "skipped: invalid file type"
                continue

            # reset file for ingest
            file.seek(0)

            # create a thread to ingest the file
            thread = threading.Thread(
                target=ingest_file,
                args=(file, outputs, idx,)
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        uploader = flask.g.user_id

        for idx, output in enumerate(outputs):
            print(f"thread #{idx}'s output:\n{output}\n", flush=True)

        return flask.jsonify({
            "message": "files received and ingested successfully",
            "uploaded_by": uploader,
        })

    return server 

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=8000,
        ssl_context=("server.crt", "server.key"),
        use_reloader=False
    )
