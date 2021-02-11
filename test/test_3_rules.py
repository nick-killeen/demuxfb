"""
Test a subset of chat construction rules against *my* current expectations.
These should not be considered formal tests. They are just an artifact of
exploratory sanity testing, distrubted only for completeness. There is no formal
spec.

This file should not be maintained. Throw it out when the Facebook exporter
updates
"""

import sys

from .helpers import SpoofChatFeed

sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position


def test_match_media_message():
    chat_feed = SpoofChatFeed()
    chat_feed.push(photos=[{'uri': 'messages/inbox/convo/photos/blah.png',
                                   'creation_timestamp': 1000}])
    chat_feed.push(content='What do these mean?',
                   photos=[{'uri': 'messages/inbox/convo/photos/blah.png',
                            'creation_timestamp': 1000},
                           {'uri': 'messages/inbox/convo/photos/blah1.png',
                            'creation_timestamp': 2000}])
    chat_feed.push(gifs=[{'uri': 'messages/inbox/convo/gifs/blah.gif'}])
    chat_feed.push(audio_files=[{'uri': 'messages/inbox/convo/audio/blah.mp4',
                                 'creation_timestamp': 1000}])
    chat_feed.push(videos=[{'uri': 'messages/inbox/convo/videos/blah.mp4',
                            'creation_timestamp': 1000,
                            'thumbnail': {
                                'uri': 'messages/inbox/convo//videos/thumbnails'
                                       '/blarg.jpg'
                            }}])
    chat_feed.push(files=[{'uri': 'messages/inbox/convo/videos/blah.mp4',
                           'creation_timestamp': 1000}])
    chat_feed.push(sticker={'uri': 'messages/stickers_used/blah.png'})

    chat = demuxfb.build_chat(chat_feed, 'John Smith')
    messages = chat.messages

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert message.content is None
    assert len(message.photos) == 1
    assert len(message.gifs) == 0
    assert len(message.audio_files) == 0
    assert len(message.videos) == 0
    assert len(message.attachment_files) == 0
    assert len(message.stickers) == 0

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert message.content == 'What do these mean?'
    assert len(message.photos) == 2

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert len(message.photos) == 0
    assert len(message.gifs) == 1

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert len(message.audio_files) == 1

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert len(message.videos) == 1

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert len(message.attachment_files) == 1

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.MediaMessage)
    assert len(message.stickers) == 1


def test_match_empty_message():
    chat_feed = SpoofChatFeed()
    chat_feed.push()

    chat = demuxfb.build_chat(chat_feed, 'John Smith')
    messages = chat.messages

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.EmptyMessage)


def test_call_messages():
    chat_feed = SpoofChatFeed()
    chat_feed.push(content='John started a video chat.')
    chat_feed.push(content='John joined the video chat.')
    chat_feed.push(content='The video chat ended.')
    chat_feed.push(content='John started a call.')
    chat_feed.push(content='John joined the call.')
    chat_feed.push(content='The call ended.')

    chat_feed.push(content='John started a call.')
    chat_feed.push(content='John joined the call.')
    chat_feed.push(content='The call ended.')

    chat = demuxfb.build_chat(chat_feed, 'Jake Smith')
    messages = chat.messages

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallStartMessage)
    assert message.call_type == demuxfb.message.CallType.VIDEO

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallJoinMessage)
    assert message.call_type == demuxfb.message.CallType.VIDEO

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallEndMessage)
    assert message.call_type == demuxfb.message.CallType.VIDEO

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallStartMessage)
    assert message.call_type == demuxfb.message.CallType.AUDIO

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallJoinMessage)
    assert message.call_type == demuxfb.message.CallType.AUDIO

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.CallEndMessage)
    assert message.call_type == demuxfb.message.CallType.AUDIO


def test_match_nickname_change_message():
    chat_feed = SpoofChatFeed()
    chat_feed.push(sender_name='Joseph',
                   content='Joseph cleared his own nickname.')
    chat_feed.push(sender_name='Joseph',
                   content='Joseph cleared your nickname.')
    chat_feed.push(sender_name='Joseph',
                   content='Joseph cleared the nickname for Jacob.')
    chat_feed.push(sender_name='Joseph',
                   content='Joseph set the nickname for Jacob to Jake.')
    chat_feed.push(sender_name='Joseph',
                   content='Joseph set your nickname to John.')
    chat_feed.push(sender_name='Joseph',
                   content='Joseph set their own nickname to Joe.')
    chat_feed.push(content='You cleared your nickname.')
    chat_feed.push(content='You cleared the nickname for Joseph.')
    chat_feed.push(content='You set the nickname for Joseph to Joe.')
    chat_feed.push(content='You set your nickname to John.')

    chat = demuxfb.build_chat(chat_feed, 'John Smith')
    messages = chat.messages

    joseph = chat.get_participant('Joseph')
    jacob = chat.get_participant('Jacob')

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject == joseph
    assert message.new_nickname is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject.is_me()
    assert message.new_nickname is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject == jacob
    assert message.new_nickname is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject == jacob
    assert message.new_nickname == 'Jake'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject.is_me()
    assert message.new_nickname == 'John'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter == joseph
    assert message.subject == joseph
    assert message.new_nickname == 'Joe'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter.is_me()
    assert message.subject.is_me()
    assert message.new_nickname is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter.is_me()
    assert message.subject == joseph
    assert message.new_nickname is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter.is_me()
    assert message.subject == joseph
    assert message.new_nickname == 'Joe'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.NicknameChangeMessage)
    assert message.setter.is_me()
    assert message.subject.is_me()
    assert message.new_nickname == 'John'


def test_match_chat_settings_change_message():
    chat_feed = SpoofChatFeed()
    chat_feed.push(content='Jacob named the group Saturday Hangout.')
    chat_feed.push(content='Jacob changed the group photo.')
    chat_feed.push(content='Jacob changed the chat theme.')
    chat_feed.push(content=r'Jacob set the emoji to \u00f0\u009f\u008d\u00ba.')
    chat_feed.push(content='Jacob turned on member approval and will review'
                           ' requests to join the group.')
    chat_feed.push(content='Jacob turned off member approval. Anyone with the'
                           ' link can join the group.')

    chat = demuxfb.build_chat(chat_feed, 'John Smith')
    messages = chat.messages

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == demuxfb.message.ChatSettingsType.CHANGE_NAME
    assert message.new_name == 'Saturday Hangout'
    assert message.new_emoji is None
    assert message.new_approval_is_required_policy is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == \
        demuxfb.message.ChatSettingsType.CHANGE_PHOTO
    assert message.new_name is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == \
        demuxfb.message.ChatSettingsType.CHANGE_THEME

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == \
        demuxfb.message.ChatSettingsType.CHANGE_EMOJI
    assert message.new_emoji == r'\u00f0\u009f\u008d\u00ba'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == \
        demuxfb.message.ChatSettingsType.CHANGE_MEMBERSHIP_POLICY
    assert message.new_approval_is_required_policy

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.ChatSettingsChangeMessage)
    assert message.settings_type == \
        demuxfb.message.ChatSettingsType.CHANGE_MEMBERSHIP_POLICY
    assert message.new_approval_is_required_policy is not None
    assert not message.new_approval_is_required_policy


def test_plan_messages():
    chat_feed = SpoofChatFeed()
    chat_feed.push(content='Joseph responded ')
    chat_feed.push(content='Jacob started a plan.')
    chat_feed.push(content='Jacob named the plan Saturday Hangout.')
    chat_feed.push(content='Jacob updated the plan to Sat, Aug 5 at 12 PM.')
    chat_feed.push(content='Joseph responded ')
    chat_feed.push(content='Jacob deleted the plan Saturday Hangout for Sat,'
                           ' Aug 5 at 12 PM.')

    chat_feed.push(content='Joseph responded ')

    chat = demuxfb.build_chat(chat_feed, 'John Smith')
    messages = chat.messages

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.TextMessage)

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.PlanCreationMessage)

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.PlanUpdateMessage)
    assert message.new_plan_title == 'Saturday Hangout'
    assert message.new_plan_time is None

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.PlanUpdateMessage)
    assert message.new_plan_title is None
    assert message.new_plan_time == 'Sat, Aug 5 at 12 PM'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.PlanRespondencyMessage)

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.PlanDeletionMessage)
    assert message.plan_title == 'Saturday Hangout'
    assert message.plan_time == 'Sat, Aug 5 at 12 PM'

    message = messages.pop(0)
    assert isinstance(message, demuxfb.message.TextMessage)
