import flask

def create_server():
    server = flask.Flask(__name__)

    @server.route("/")
    def root():
        return "hello from create_server!"

    @server.route("/health")
    def health():
        print("/health: ping~!", flush=True)
        return "Ok"

    return server 

if __name__ == "__main__":
    server = create_server()
    server.run(
        host="0.0.0.0",
        port=7000,
        use_reloader=False
    )
