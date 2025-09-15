import flask

def create_server():
    server = flask.Flask(__name__)
    db_bp = flask.Blueprint("db", __name__)

    @db_bp.route("/health")
    def health():
        print("/health: ping~!", flush=True)
        return "Ok"

    server.register_blueprint(db_bp, url_prefix="/db")

    return server

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=6000,
        use_reloader=False
    )
