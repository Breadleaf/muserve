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
        con = db_handler.con
        try:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s);",
                (username, email)
            )
            con.commit()
            cur.close()
        except psycopg2.Error as e:
            return "Failed to add to db :("
        return "Done!"

    # TODO: remove
    # NOTE: here to test connections to the db
    @server.route("/get")
    def get():
        con = db_handler.con
        try:
            cur = con.cursor()
            cur.execute("SELECT * FROM users;")
            res = cur.fetchall()
            cur.close()
        except psycopg2.Error as e:
            return "Failed to get from db :("
        return "\n".join(str(res))

    return server 

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=8000,
        ssl_context=("server.crt", "server.key"),
        use_reloader=False
    )
