import magic

import subprocess
import io
import sys

class MusicHandler:
    def __init__(self, allowed):
        self.magic = magic.Magic(mime=True)
        self.allowed = allowed # mimetypes

    def validate_file(self, file):
        real_mimetype = self.magic.from_buffer(file)
        return real_mimetype in self.allowed

    def convert_file(self, path, raw_name):
        bitrates = ["64k", "128k", "320k"]
        args = ["/bin/ffmpeg", "-i", path, "-c:a", "libvorbis", "-b:a"]

        file_buffers = {}
        for bitrate in bitrates:
            new_path = f"{path}_{bitrate}.ogg"

            # process file with ffmpeg
            process = subprocess.Popen(
                args + [bitrate, new_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # check if process failed
            stdout, stderr = process.communicate()
            exit_code = process.wait()

            if exit_code != 0:
                return None, stdout, f"error converting file: '{new_path}'\nerror: '{stderr}'"

            # read file into buffer
            try:
                with open(new_path, "rb") as file:
                    buf = io.BytesIO(file.read())
                file_buffers[f"{bitrate}_{raw_name}.ogg"] = buf
            except FileNotFoundError:
                return None, "", f"file not found: '{new_path}'"

        return file_buffers, stdout, stderr
