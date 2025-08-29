import flask
import threading
import logging
import queue
import time

class Server:
    def __init__(self, command_queue=None, log_handler=None):
        self.app = flask.Flask(__name__)
        self.command_queue = command_queue or queue.Queue()
        self._shutdown_flag = threading.Event()

        if log_handler:
            handler = logging.StreamHandler(log_handler)
            handler.setLevel(logging.INFO)
            self.app.logger.addHandler(handler)
            self.app.logger.setLevel(logging.INFO)

        @self.app.route("/")
        def home():
            return "Hello ~"

    def _run_flask(self):
        self.app.run(
            host="0.0.0.0",
            port=8000,
            ssl_context=("server.crt", "server.key"),
            use_reloader=False
        )

    def _monitor_commands(self):
        while not self._shutdown_flag.is_set():
            try:
                command = self.command_queue.get(timeout=1)
                if command == "shutdown":
                    print("[SERVER]: Received shutdown command")
                    self._shutdown_flag.set()
            except queue.Empty:
                continue

    def start(self):
        # start the command listener
        threading.Thread(target=self._monitor_commands, daemon=True).start()

        # start the flask server in a thread
        self.flask_thread = threading.Thread(target=self._run_flask, daemon=True)
        self.flask_thread.start()

    def stop(self):
        self._shutdown_flag.set()

if __name__ == "__main__":
    server = Server()
    server.start()
    while True:
        pass
