import flask

def create_server():
    server = flask.Flask(__name__)
    store_bp = flask.Blueprint("store", __name__)

    @store_bp.route("/health")
    def health():
        print("/health: ping~!", flush=True)
        return "Ok"

    server.register_blueprint(store_bp, url_prefix="/store")

    return server

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )
