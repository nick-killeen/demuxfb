"""Test the construction of ChatFeeds."""

import pytest
import sys
from pathlib import Path

sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position


single_file_messages = [
    {
        'sender_name': 'Henry',
        'timestamp_ms': 1306315450000,
        'content': 'Hey',
        'type': 'Generic'
    },
    {
        'sender_name': 'Daniel',
        'timestamp_ms': 1306316867000,
        'content': 'Hey how are you?',
        'type': 'Generic'
    },
    {
        'sender_name': 'Henry',
        'timestamp_ms': 1566296834426,
        'content': 'How are you?',
        'type': 'Generic'
    },
    {
        'sender_name': 'Daniel',
        'timestamp_ms': 1566296938824,
        'content': 'Doing alright',
        'type': 'Generic'
    },
    {
        'sender_name': 'Daniel',
        'timestamp_ms': 1566296943820,
        'content': 'You?',
        'type': 'Generic'
    }
]


def test_file_feed():
    file = Path('test/data/chats/messages.json')
    chat_feed = demuxfb.ChatFileFeed(file)

    messages = list(chat_feed.message_json_iter())
    assert messages == single_file_messages


def test_file_feed_invalid_path():
    with pytest.raises(demuxfb.InvalidChatFeedException) as einfo:
        file = Path('test/data/chats/hello')
        demuxfb.ChatFileFeed(file)
    assert str(einfo.value).startswith('Could not read json stream from file')


def test_file_feed_not_json():
    with pytest.raises(demuxfb.InvalidChatFeedException) as einfo:
        file = Path('test/data/chats/notjson.txt')
        demuxfb.ChatFileFeed(file)
    assert str(einfo.value).startswith('Could not read json stream from file')


# Make sure that files like 'message_2.json' and 'message_10.json' are sorted
# and joined numerically rather than alphabetically.
def test_folder_feed_order():
    folder = Path('test/data/chats/hello')
    chat_feed = demuxfb.ChatFolderFeed(folder)

    messages = list(chat_feed.message_json_iter())
    assert len(messages) == 46
    timestamps = [message['timestamp_ms'] for message in messages]
    assert timestamps == sorted(timestamps)


def test_folder_feed_not_a_folder():
    with pytest.raises(demuxfb.InvalidChatFeedException) as einfo:
        file = Path('test/data/chats/messages.json')
        demuxfb.ChatFolderFeed(file)
    assert str(einfo.value).startswith(
        'Could not create folder feed; not a folder')


def test_folder_feed_contains_bad_name():
    with pytest.raises(demuxfb.InvalidChatFeedException) as einfo:
        file = Path('test/data/chats/badname')
        demuxfb.ChatFolderFeed(file)
    assert str(einfo.value).endswith(
        'does not fit expected message_NUM.json format')
