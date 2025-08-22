import flask

class Server:
    def __init__(self):
        self.app = flask.Flask(__name__)

        @self.app.route("/")
        def home():
            return "Hello ~"

    def start(self):
        self.app.run(
            host="0.0.0.0",
            port=8000,
            ssl_context=("server.crt", "server.key")
        )
