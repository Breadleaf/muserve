import flask

import DatabaseHandler
import MusicHandler

def create_server():
    server = flask.Flask(__name__)

    db_handler = DatabaseHandler.DatabaseHandler()
    music_handler = MusicHandler.MusicHandler(["audio/mpeg"])

    @server.route("/")
    def root():
        return "hello from create_server!"

    # TODO: remove
    # NOTE: here to test connections to the db
    @server.route("/add_user/<username>/<email>")
    def add_user(username, email):
        err = db_handler.insert(
            "INSERT INTO users (name, email) VALUES (%s, %s);",
            (username, email)
        )

        return err if err else "Done!"

    # TODO: remove
    # NOTE: here to test connections to the db
    @server.route("/get_users")
    def get_users():
        (ok, res) = db_handler.fetch(
            "SELECT * FROM users;",
        )

        # res stores an error if ok is False
        return "\n".join(str(res)) if ok else res

    @server.route("/upload")
    def upload():
        return flask.render_template("upload.html")

    @server.route("/send", methods=["POST"])
    def send():
        uploaded_files = list(flask.request.files.values())

        if not uploaded_files:
            return flask.jsonify({"error": "no files uploaded"}), 400

        file_info = []
        for file in uploaded_files:
            if file.filename:
                file_contents = file.read()

                valid_file_type = music_handler.validate_file(file_contents)

                if valid_file_type:
                    # TODO: remove this line
                    file.save(f"./{file.filename}")

                # ignore will prevent program from crashing if an UTF-8 character is found
                snippet = file_contents[:50].decode("utf-8", "ignore")

                file_info.append({
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(file_contents),
                    "snippet": snippet,
                })

        for fi in file_info:
            print(f"file info: {fi}\nvalid mimetype: {valid_file_type}")

        return flask.jsonify({"message": "files received successfully"})

    return server 

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=8000,
        ssl_context=("server.crt", "server.key"),
        use_reloader=False
    )
