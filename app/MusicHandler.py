import magic

import subprocess
import io
import typing

FILE_CONVERSION_TYPE = typing.Tuple[
    None | typing.Mapping[str, io.BytesIO],
    None | str,
    None | str,
]

class MusicHandler:
    def __init__(self, allowed):
        self.magic = magic.Magic(mime=True)
        self.allowed = allowed # mimetypes

    def validate_file(self, file_content: bytes) -> bool:
        """
        Check if a file's real mimetype is in the set of allowed mimetypes

        Input:
        file_content: string form of the file's content to check
        """

        real_mimetype = self.magic.from_buffer(file_content)
        return real_mimetype in self.allowed

    def convert_file(self, path: str, raw_name: str) -> FILE_CONVERSION_TYPE:
        """
        Convert a file to various bitrates of vorbis ogg

        Inputs:
        path: path to the file, ex: "/tmp/1234/my_song.mp3"
        raw_name: name of file without extension, ex: "my_song"

        Output:
        'tuple of: map or null, string or null, string or null'
        (
            map[str, io.BytesIO]?, # f"{bitrate}_{raw_name}.ogg" -> file in ram
            str?, stdout of subprocess.Popen(...) for ffmpeg
            str?, stderr of subprocess.Popen(...) for ffmpeg
        )

        NOTE: stdout and stderr are 'None' on fully successful conversion
        """

        bitrates = ["64k", "128k", "320k"]
        args = ["/bin/ffmpeg", "-i", path, "-c:a", "libvorbis", "-b:a"]

        file_buffers: typing.Mapping[str, io.BytesIO] = {}
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
                return None, str(stdout), f"error converting file: '{new_path}'\nerror: '{stderr}'"

            # read file into buffer
            try:
                with open(new_path, "rb") as file:
                    buf = io.BytesIO(file.read())
                file_buffers[f"{bitrate}_{raw_name}.ogg"] = buf

            except FileNotFoundError:
                return None, None, f"file not found: '{new_path}'"

        return file_buffers, None, None
