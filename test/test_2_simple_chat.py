"""
Test that the rule-application process correctly orchestrates the construction
of some simple test chats.
"""

import sys

from .helpers import SpoofChatFeed


sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position


def test_basic():
    chat_feed = SpoofChatFeed()
    chat_feed.push(sender_name='Jason', content='Hello Milly')
    chat_feed.push(sender_name='Milly', content='Hi', )
    chat_feed.push(sender_name='Jason',
                   content='You set the nickname for Milly to M.')
    chat_feed.push(sender_name='Milly', content='M set your nickname to J.')
    chat_feed.push(sender_name='Milly',
                   content='M set the nickname for Wendy to W.')

    chat = demuxfb.build_chat(chat_feed, 'Jason')
    messages = chat.messages
    jason = chat.get_participant('Jason')
    milly = chat.get_participant('Milly')
    wendy = chat.get_participant('Wendy')

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.TextMessage)
    assert message.content == 'Hello Milly'
    assert message.sender == jason

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.TextMessage)
    assert message.content == 'Hi'
    assert message.sender == milly

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.sender == jason
    assert message.setter == jason
    assert message.subject == milly
    assert message.new_nickname == 'M'

    assert chat.participants == {jason, milly, wendy}
