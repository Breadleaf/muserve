import magic

class MusicHandler:
    def __init__(self, allowed):
        self.magic = magic.Magic(mime=True)
        self.allowed = allowed # mimetypes

    def validate_file(self, file):
        real_mimetype = self.magic.from_buffer(file)
        return real_mimetype in self.allowed
