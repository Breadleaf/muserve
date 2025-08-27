import textual.app as ta
import textual.widgets as tw
import textual.containers as tc
import textual.reactive as tr

import io
import queue

import Server

class DashboardApp(ta.App):
    CSS = """
        Screen {
            layout: vertical;
            align: center middle;
        }

        #log-title {
            height: 1;
        }

        #log-box {
            height: 20;
            width: 80%;
            border: solid white;
            overflow: scroll;
        }

        #command-input {
            width: 80%;
            border: solid green;
        }

        #send-btn {
            width: 20;
            align: center middle;
        }
        """

    log_buffer = tr.reactive("")

    def __init__(self):
        super().__init__()
        self.log_stream = io.StringIO()
        self.command_queue = queue.Queue()
        self.server = Server.Server(
            command_queue=self.command_queue,
            log_handler=self.log_stream
        )

    def compose(self):
        yield tc.Vertical(
            tw.Static("Flask Server Logs:", id="log-title"),
            tw.Static(self.log_buffer, id="log-box"),
            tw.Input(placeholder="Enter command (e.g. shutdown)", id="command-input"),
            tw.Button("Send", id="send-btn")
        )

    async def on_mount(self):
        self.server.start()
        self.set_interval(1, self.update_log_box)

    def update_log_box(self):
        self.log_buffer = self.log_stream.getvalue()
        self.query_one("#log-box", tw.Static).update(self.log_buffer)

    async def on_button_pressed(self, event):
        if event.button.id == "send-btn":
            input_widget = self.query_one("#command-input", tw.Input)
            command = input_widget.value.strip().lower()
            if command:
                self.command_queue.put(command)
                if command == "shutdown":
                    self.exit()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
