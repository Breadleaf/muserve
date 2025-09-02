import flask

import DatabaseHandler

def create_server():
    server = flask.Flask(__name__)

    db_handler = DatabaseHandler.DatabaseHandler()

    @server.route("/")
    def root():
        return "hello from create_server!"

    # TODO: remove
    # NOTE: here to test connections to the db
    @server.route("/add/<username>/<email>")
    def add(username, email):
        err = db_handler.insert(
            "INSERT INTO users (name, email) VALUES (%s, %s);",
            (username, email)
        )

        return err if err else "Done!"

    # TODO: remove
    # NOTE: here to test connections to the db
    @server.route("/get")
    def get():
        (ok, res) = db_handler.fetch(
            "SELECT * FROM users;",
        )

        # res stores an error if ok is False
        return "\n".join(str(res)) if ok else res

    return server 

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=8000,
        ssl_context=("server.crt", "server.key"),
        use_reloader=False
    )
