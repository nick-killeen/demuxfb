"""Module to define types of message structures to generate."""

from abc import ABC as _ABC
from typing import Optional as _Optional, List as _List
from enum import Enum as _Enum, auto as _auto

from ._reaction import Reaction as _Reaction
from ._participant import Participant as _Participant
from . import media as _media


class Message(_ABC):
    timestamp: int
    content: _Optional[str]
    sender: _Participant
    reactions: _List[_Reaction]
    message_json: dict


class UnrecognizedMessage(Message):
    """
    Instances of this class are generated when a JSON message does not match any
    existing rules.
    """
    pass


class MediaMessage(Message):
    photos: _List[_media.Photo]
    gifs: _List[_media.Gif]
    audio_files: _List[_media.AudioFile]
    videos: _List[_media.Video]
    stickers: _List[_media.Sticker]
    attachment_files: _List[_media.AttachmentFile]


class EmptyMessage(Message):
    pass


class CallType(_Enum):
    # An audio call with optional video sharing.
    CALL = _auto()
    # A video call.
    VIDEO = _auto()


class CallStartMessage(Message):
    call_type: CallType


class CallJoinMessage(Message):
    call_type: CallType


class CallShareVideoMessage(Message):
    pass


class CallEndMessage(Message):
    call_type: CallType


class NicknameChangeMessage(Message):
    new_nickname: _Optional[str]
    setter: _Participant
    subject: _Participant


class TextMessage(Message):
    pass


class SubscribeMessage(Message):
    inviter: _Participant
    # `invitees` may fail to contain the appropriate amount of unkown
    # participants.
    invitees: _List[_Participant]


class UnsubscribeMessage(Message):
    removed_self: bool
    removalist: _Participant
    removed: _Participant


class WaveMessage(Message):
    pass


class AppChallengeMessage(Message):
    app_name: str


class AppNewScoreMessage(Message):
    app_name: str
    score: str
    personal_best: bool


class AppLeaderboardReshuffleMessage(Message):
    app_name: str
    now_in_first_place: bool


class LinkMessage(Message):
    shared_link: _Optional[str]


class PlanCreationMessage(Message):
    pass


class PlanUpdateMessage(Message):
    new_plan_title: _Optional[str]
    new_plan_date_time: _Optional[str]


class PlanDeletionMessage(Message):
    # The name of the plan that has been deleted.
    plan_title: _Optional[str]
    # The date and time the plan would have occurred, had it not been deleted.
    plan_date_time: str


class PlanRespondencyMessage(Message):
    pass


class PlanReminderMessage(Message):
    is_concurrent: bool
    plan_title: _Optional[str]
    plan_hour: str


class PollCreationMessage(Message):
    poll_name: str


class PollAddVoteMessage(Message):
    poll_name: str
    vote_option: str
    hidden_vote_count: int


class PollRemoveVoteMessage(Message):
    poll_name: str
    vote_option: str
    hidden_vote_count: int


class PollChangeVoteMessage(Message):
    poll_name: str
    vote_option: str


class PollExpiredMessage(Message):
    pass


class AdminAddMessage(Message):
    instigator: _Participant
    subject: _Participant


class AdminRemoveMessage(Message):
    instigator: _Participant
    subject: _Participant


class ChatSettingsType(_Enum):
    CHANGE_THEME = _auto()
    CHANGE_EMOJI = _auto()
    CHANGE_MEMBERSHIP_POLICY = _auto()
    CHANGE_NAME = _auto()
    CHANGE_PHOTO = _auto()


class ChatSettingsChangeMessage(Message):
    settings_type: ChatSettingsType
    new_name: _Optional[str]
    new_emoji: _Optional[str]
    new_approval_is_required_policy: _Optional[bool]


__all__ = [n for n in globals() if n[0] != '_']
