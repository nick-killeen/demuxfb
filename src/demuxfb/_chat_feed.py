"""
Module for logic about interpreting chat archives on disk (and an interface for
elsewhere) as json feeds.
"""

from typing import Iterator, List, Callable
from abc import ABC, abstractmethod
from pathlib import Path
import re

import json
import itertools


# Apply some 'func' transformation to all string keys and values of a json
# object.
def _json_recursive_apply(o: object, func: Callable[[str], str]) -> object:
    if isinstance(o, dict):
        for key in o:
            o[func(key)] = _json_recursive_apply(o[key], func)
        return o
    elif isinstance(o, list):
        for i in range(len(o)):
            o[i] = _json_recursive_apply(o[i], func)
        return o
    elif isinstance(o, str):
        return func(o)
    return o


class ChatFeed(ABC):
    """
    Interface for an adapter to extract a chat's json data from some type of
    source. Expected by `demuxfb.build_chat`.

    See Also
    --------
    demuxfb.ChatFileFeed
    demuxfb.ChatFolderFeed
    """

    @abstractmethod
    def message_json_iter(self) -> Iterator[dict]:
        """
        Return an iterator through all of the json messages in the chat,
        oldest first.

        Returns
        -------
        Iterator[dict]
            An iterator over the json messages in the chat, oldest first.
        """
        raise NotImplementedError


class InvalidChatFeedException(Exception):
    """Error for when `ChatFeed` construction fails."""
    pass


class ChatFileFeed(ChatFeed):
    """Adapter to extract a chat's json data from a single json file."""

    def __init__(self, file: Path) -> None:
        """
        Build feed from a json file.

        Parameters
        ----------
        file : pathlib.Path
            Path to a json file representing the chat, as exported by the
            'Download Your Information' Facebook feature. The file must be
            unzipped.

        Raises
        ------
        InvalidChatFeedException
            If the file cannot be opened for reading, or cannot be parsed as
            json.
        """

        try:
            with file.open('r') as file_io:
                file_str = file_io.read()
                self._json = json.loads(file_str)

                # The file's contents are encoded with one UTF-8 code point per
                # character (which is a strange format), like:
                #   {"place": "Ch\u00c3\u00a2teau d\u00e2\u0080\u0099If"}.
                # Passing this through the json loader yields a garbled value
                #   'ChÃ¢teau dâ\x80\x99If'.
                # But by encoding this in latin1 (1-byte per character), we can
                # recover
                #   b'Ch\xc3\xa2teau d\xe2\x80\x99If',
                # which is a raw form conducive to correct multi-bytes-per-char
                # decoding, yielding
                #  'Château d’If'
                _json_recursive_apply(self._json,
                                      lambda s: s.encode('latin1').decode())

        except Exception as e:
            raise InvalidChatFeedException(
                'Could not read json stream from file: ' + file.name) from e

    def message_json_iter(self) -> Iterator[dict]:
        return reversed(self._json['messages'])


class ChatFolderFeed(ChatFeed):
    """
    Adapter to extract a chat's json data from a folder of `message_1.json`,
    `message_2.json`, ... files.
    """

    _file_feeds: List[ChatFileFeed]

    def __init__(self, folder: Path) -> None:
        """
        Build feed from a folder of json files.

        Parameters
        ----------
        folder : pathlib.Path
            Path to a directory of json files representing the chat, as exported
            by the 'Download Your Information' Facebook feature. The folder must
            be unzipped, and contain some number of files exactly of the names
            `message_1.json`, `message_2.json`, ...

        Raises
        ------
        InvalidChatFeedException
            - If `folder` is not a directory, is empty, does not contain solely
            'message_<NUM>.json' files; or if any subfile cannot be opened for
            reading or cannot be parsed as json.
        """
        if not folder.is_dir():
            raise InvalidChatFeedException('Could not create folder feed; not'
                                           ' a folder: ' + str(folder.name))

        # Use list so that we can iterate through multiple times.
        files = [file for file in list(folder.iterdir()) if not file.is_dir()]
        if files == []:
            raise InvalidChatFeedException('Could not create feed from empty '
                                           'folder: ' + str(folder.name))
        for file in files:
            if re.match(r'message_(\d+)\.json$', file.name) is None:
                raise InvalidChatFeedException(
                    "Chat folder '" + str(folder.name) + "' contains the file '"
                    + str(file.name) + "', which does not fit expected"
                    ' message_NUM.json format')

        # Alphabetic sorting will fail, so sort numerically.
        def part_number(file: Path) -> int:
            return int(re.match(r'message_(\d+)\.json$', file.name)[1])

        self._file_feeds = []
        for file in sorted(files, key=part_number, reverse=True):
            file_feed = ChatFileFeed(file)
            self._file_feeds.append(file_feed)

    def message_json_iter(self) -> Iterator[dict]:
        file_feed_iterators = [file_feed.message_json_iter()
                               for file_feed in self._file_feeds]
        return itertools.chain.from_iterable(file_feed_iterators)
