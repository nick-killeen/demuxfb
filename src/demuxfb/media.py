"""Module to define media types a message can contain."""

__all__ = ['Photo', 'Gif', 'Sticker', 'AudioFile', 'Video', 'AttachmentFile']


class Photo:
    uri: str
    creation_timestamp: int

    def __init__(self, photo_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = photo_json['uri']
        self.creation_timestamp = int(photo_json['creation_timestamp']) * 1000


class Gif:
    uri: str

    def __init__(self, gif_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = gif_json['uri']


class Sticker:
    uri: str

    def __init__(self, sticker_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = sticker_json['uri']


class AudioFile:
    uri: str
    creation_timestamp: int

    def __init__(self, audio_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = audio_json['uri']
        self.creation_timestamp = int(
            audio_json['creation_timestamp']) * 1000


class Video:
    uri: str
    thumbnail_uri: str
    creation_timestamp: int

    def __init__(self, video_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = video_json['uri']
        self.thumbnail_uri = video_json['thumbnail']['uri']
        self.creation_timestamp = int(video_json['creation_timestamp']) * 1000


class AttachmentFile:
    uri: str
    creation_timestamp: int

    def __init__(self, attachment_file_json: dict) -> None:
        """This method should not be called publicly."""
        self.uri = attachment_file_json['uri']
        self.creation_timestamp = int(attachment_file_json['creation_timestamp']
                                      ) * 1000
