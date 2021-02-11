"""Helpers for testing."""

from typing import Iterator, List, Any
import sys
sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position


class SpoofChatFeed(demuxfb.ChatFeed):
    _message_jsons: List[dict]
    _next_timestamp: int

    def __init__(self):
        self._message_jsons = []
        self._next_timestamp = 0

    def push_from_json(self, message_json: dict):
        self._message_jsons.append(message_json)

    def push(self, **kwargs: Any):
        """Push a json message, providing defaults for brevity."""
        json_message = kwargs
        if json_message.get('sender_name') is None:
            json_message['sender_name'] = 'John Smith'
        if json_message.get('type') is None:
            json_message['type'] = 'Generic'
        if json_message.get('timestamp_ms') is None:
            json_message['timestamp_ms'] = self._next_timestamp
        self._next_timestamp = json_message['timestamp_ms'] + 1000
        self.push_from_json(json_message)

    def message_json_iter(self) -> Iterator[dict]:
        return self._message_jsons
