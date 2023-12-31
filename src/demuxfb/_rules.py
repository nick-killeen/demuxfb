"""Module to define message-generation rules."""

from typing import Optional, Callable, List, TYPE_CHECKING

from ._tokens import _Tok
from . import message as msg
from . import media

if TYPE_CHECKING:
    from ._chat import _ChatFactory


_Rule = Callable[['_ChatFactory'], Optional[msg.Message]]


class _Ruleset:
    """An ordered collection of message generation rules."""
    _rules: List[_Rule]

    def __init__(self, rules: List[_Rule]) -> None:
        self._rules = rules

    def apply(self, chat_factory: '_ChatFactory') -> msg.Message:
        for rule in self._rules:
            maybe_message = rule(chat_factory)
            if maybe_message is not None:
                return maybe_message

        return chat_factory.make_common(msg.UnrecognizedMessage)


_all_rules: List[_Rule] = []


def _register_rule() -> Callable[[_Rule], None]:
    """
    Decorator to register a rule in the _all_rules list. The order rules are
    registered in will be their precedence.
    """
    def inner(rule: _Rule) -> None:
        global _all_rules
        _all_rules.append(rule)
    return inner


@_register_rule()
def _match_media_message(cf: '_ChatFactory'
                         ) -> Optional[msg.MediaMessage]:
    if any([cf.message_json.get(key) is not None
            for key in ['photos', 'gifs', 'audio_files', 'videos', 'sticker',
                        'files']]):
        message = cf.make_common(msg.MediaMessage)

        message.photos = [media.Photo(json)
                          for json in cf.message_json.get('photos') or []]
        message.gifs = [media.Gif(json)
                        for json in cf.message_json.get('gifs') or []]
        message.audio_files = [media.AudioFile(
            json) for json in cf.message_json.get('audio_files') or []]
        message.videos = [media.Video(json)
                          for json in cf.message_json.get('videos') or []]
        message.attachment_files = [media.AttachmentFile(
            json) for json in cf.message_json.get('files') or []]

        if cf.message_json.get('sticker') is None:
            message.stickers = []
        else:
            message.stickers = [media.Sticker(cf.message_json['sticker'])]

        return message
    return None


@_register_rule()
def _match_empty_message(cf: '_ChatFactory'
                         ) -> Optional[msg.EmptyMessage]:
    if 'content' not in cf.message_json:
        message = cf.make_common(msg.EmptyMessage)
        return message

    return None


@_register_rule()
def _match_call_start_message(cf: '_ChatFactory'
                              ) -> Optional[msg.CallStartMessage]:
    if cf.state.call_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, r' started a video chat\.']):
        cf.state.call_is_active = True
        message = cf.make_common(msg.CallStartMessage)
        message.call_type = msg.CallType.VIDEO
        return message

    if cf.match([_Tok.SENDER_ALIAS, r' started a call\.']):
        cf.state.call_is_active = True
        message = cf.make_common(msg.CallStartMessage)
        message.call_type = msg.CallType.CALL
        return message

    return None


@_register_rule()
def _match_call_join_message(cf: '_ChatFactory'
                             ) -> Optional[msg.CallJoinMessage]:
    if not cf.state.call_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, r' joined the video chat\.']):
        message = cf.make_common(msg.CallJoinMessage)
        message.call_type = msg.CallType.VIDEO
        return message

    if cf.match([_Tok.SENDER_ALIAS, r' joined the call\.']):
        message = cf.make_common(msg.CallJoinMessage)
        message.call_type = msg.CallType.CALL
        return message

    return None


@_register_rule()
def _match_call_share_video_message(cf: '_ChatFactory'
                                    ) -> Optional[msg.CallShareVideoMessage]:
    if not cf.state.call_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, r' started sharing video\.']):
        message = cf.make_common(msg.CallJoinMessage)
        message = cf.make_common(msg.CallShareVideoMessage)
        return message

    return None


@_register_rule()
def _match_call_end_message(cf: '_ChatFactory'
                            ) -> Optional[msg.CallEndMessage]:
    if not cf.state.call_is_active:
        return None

    if cf.match([r'The video chat ended\.']):
        cf.state.call_is_active = False
        message = cf.make_common(msg.CallEndMessage)
        message.call_type = msg.CallType.VIDEO
        return message

    if cf.match([r'The call ended\.']):
        cf.state.call_is_active = False
        message = cf.make_common(msg.CallEndMessage)
        message.call_type = msg.CallType.CALL
        return message

    return None


@_register_rule()
def _match_nickname_change_message(cf: '_ChatFactory'
                                   ) -> Optional[msg.NicknameChangeMessage]:
    if cf.match([_Tok.SENDER_ALIAS, r' cleared (?:his|her|their) own nickname\.'
                 ]):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = None
        message.setter = message.sender
        message.subject = message.sender
        return message

    if cf.match([_Tok.SENDER_ALIAS, r' cleared your nickname\.']):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = None
        message.setter = message.sender
        message.subject = cf.participant_manager.request_me()
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' cleared the nickname for ',
                 _Tok.PARTICIPANT_NAME]):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = None
        message.setter = message.sender
        message.subject = cf.participant_manager.request_participant(
            cf.captures[_Tok.PARTICIPANT_NAME])
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' set the nickname for ',
                 _Tok.PARTICIPANT_NAME, ' to ', _Tok.ANYTHING]):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = cf.captures[_Tok.ANYTHING]
        message.setter = message.sender
        message.subject = cf.participant_manager.request_participant(
            cf.captures[_Tok.PARTICIPANT_NAME])
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' set your nickname to ', _Tok.ANYTHING]):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = cf.captures[_Tok.ANYTHING]
        message.setter = message.sender
        message.subject = cf.participant_manager.request_me()
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' set (?:his|her|their) own nickname to ',
                 _Tok.ANYTHING]):
        message = cf.make_common(msg.NicknameChangeMessage)
        message.new_nickname = cf.captures[_Tok.ANYTHING]
        message.setter = message.sender
        message.subject = message.sender
        return message

    return None


@_register_rule()
def _match_chat_settings_change_message(
        cf: '_ChatFactory') -> Optional[msg.ChatSettingsChangeMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' named the group ', _Tok.ANYTHING]):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_NAME
        message.new_name = cf.captures[_Tok.ANYTHING]
        message.new_emoji = None
        message.new_approval_is_required_policy = None
        return message

    if cf.match([_Tok.SENDER_ALIAS, r' changed the group photo\.']):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_PHOTO
        message.new_name = None
        message.new_emoji = None
        message.new_approval_is_required_policy = None
        return message

    if cf.match([_Tok.SENDER_ALIAS, r' changed the chat theme\.']):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_THEME
        message.new_name = None
        message.new_emoji = None
        message.new_approval_is_required_policy = None
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' set the emoji to ', _Tok.EMOJI]):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_EMOJI
        message.new_name = None
        message.new_emoji = cf.captures[_Tok.EMOJI]
        message.new_approval_is_required_policy = None
        return message

    if cf.match([_Tok.SENDER_ALIAS,
                 r' turned on member approval and will review requests to join'
                 r' the group\.']):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_MEMBERSHIP_POLICY
        message.new_name = None
        message.new_emoji = None
        message.new_approval_is_required_policy = True
        return message

    if cf.match([_Tok.SENDER_ALIAS,
                 r' turned off member approval\. Anyone with the link can join'
                 r' the group\.']):
        message = cf.make_common(msg.ChatSettingsChangeMessage)
        message.settings_type = msg.ChatSettingsType.CHANGE_MEMBERSHIP_POLICY
        message.new_name = None
        message.new_emoji = None
        message.new_approval_is_required_policy = False
        return message

    return None


@_register_rule()
def _match_plan_creation_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PlanCreationMessage]:
    if cf.state.plan_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, r' started a plan\.']):
        cf.state.plan_is_active = True

        message = cf.make_common(msg.PlanCreationMessage)
        return message

    return None


@_register_rule()
def _match_plan_update_message(cf: '_ChatFactory'
                               ) -> Optional[msg.PlanUpdateMessage]:
    if not cf.state.plan_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, ' named the plan ', _Tok.ANYTHING]):
        message = cf.make_common(msg.PlanUpdateMessage)
        message.new_plan_title = cf.captures[_Tok.ANYTHING]
        message.new_plan_date_time = None
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' updated the plan to ',
                 _Tok.PLAN_DATE_TIME]):
        message = cf.make_common(msg.PlanUpdateMessage)
        message.new_plan_title = None
        message.new_plan_date_time = cf.captures[_Tok.PLAN_DATE_TIME]
        return message

    return None


@_register_rule()
def _match_plan_deletion_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PlanDeletionMessage]:
    if not cf.state.plan_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, ' deleted the plan ', _Tok.PLAN_TITLE,
                 ' for ',  _Tok.PLAN_DATE_TIME]):
        cf.state.plan_is_active = False
        message = cf.make_common(msg.PlanDeletionMessage)
        message.plan_title = cf.captures[_Tok.PLAN_TITLE]
        message.plan_date_time = cf.captures[_Tok.PLAN_DATE_TIME]
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' deleted the plan for ',
                 _Tok.PLAN_DATE_TIME]):
        cf.state.plan_is_active = False
        message = cf.make_common(msg.PlanDeletionMessage)
        message.plan_title = None
        message.plan_date_time = cf.captures[_Tok.PLAN_DATE_TIME]
        return message

    return None


@_register_rule()
def _match_plan_respondency_message(cf: '_ChatFactory'
                                    ) -> Optional[msg.PlanRespondencyMessage]:
    if not cf.state.plan_is_active:
        return None

    if cf.match([_Tok.SENDER_ALIAS, ' responded ']):
        message = cf.make_common(msg.PlanRespondencyMessage)
        return message

    return None


@_register_rule()
def _match_plan_reminder_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PlanReminderMessage]:
    if not cf.state.plan_is_active:
        return None

    if cf.match(['Reminder, 30 minutes until ', _Tok.PLAN_TIME, r'\.']):
        message = cf.make_common(msg.PlanReminderMessage)
        message.is_concurrent = False
        message.plan_title = None
        message.plan_hour = cf.captures[_Tok.PLAN_TIME]
        return message

    if cf.match(['Reminder, 30 minutes until ', _Tok.PLAN_TITLE, ' at ',
                 _Tok.PLAN_TIME]):
        message = cf.make_common(msg.PlanReminderMessage)
        message.is_concurrent = False
        message.plan_title = cf.captures[_Tok.PLAN_TITLE]
        message.plan_hour = cf.captures[_Tok.PLAN_TIME]
        return message

    if cf.match(['Reminder at ', _Tok.PLAN_TIME, r'\.']):
        cf.state.plan_is_active = False
        message = cf.make_common(msg.PlanReminderMessage)
        message.is_concurrent = True
        message.plan_title = None
        message.plan_hour = cf.captures[_Tok.PLAN_TIME]
        return message

    if cf.match(['Reminder, ', _Tok.PLAN_TITLE, ' at ', _Tok.PLAN_TIME]):
        cf.state.plan_is_active = False
        message = cf.make_common(msg.PlanReminderMessage)
        message.is_concurrent = True
        message.plan_title = cf.captures[_Tok.PLAN_TITLE]
        message.plan_hour = cf.captures[_Tok.PLAN_TIME]
        return message

    return None


@_register_rule()
def _match_poll_creation_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PollCreationMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' created a poll: ', _Tok.ANYTHING]):
        message = cf.make_common(msg.PollCreationMessage)
        message.poll_name = cf.captures[_Tok.ANYTHING]
        return message

    return None


@_register_rule()
def _match_poll_add_vote_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PollAddVoteMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' voted for "', _Tok.POLL_OPTION, '" and ',
                 _Tok.NUMBER, ' other options? in the poll: ', _Tok.POLL_NAME]):
        message = cf.make_common(msg.PollAddVoteMessage)
        message.poll_name = cf.captures[_Tok.POLL_NAME]
        message.vote_option = cf.captures[_Tok.POLL_OPTION]
        message.hidden_vote_count = int(cf.captures[_Tok.NUMBER])
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' voted for "', _Tok.POLL_OPTION,
                 '" in the poll: ', _Tok.POLL_NAME]):
        message = cf.make_common(msg.PollAddVoteMessage)
        message.poll_name = cf.captures[_Tok.POLL_NAME]
        message.vote_option = cf.captures[_Tok.POLL_OPTION]
        message.hidden_vote_count = 0
        return message

    return None


@_register_rule()
def _match_poll_remove_vote_message(cf: '_ChatFactory'
                                    ) -> Optional[msg.PollRemoveVoteMessage]:
    if cf.match([_Tok.SENDER_ALIAS,
                 ' removed (?:your |his |her |their )?vote for "',
                 _Tok.POLL_OPTION, '" and ', _Tok.NUMBER,
                 ' other options? in the poll: ', _Tok.POLL_NAME]):
        message = cf.make_common(msg.PollRemoveVoteMessage)
        message.poll_name = cf.captures[_Tok.POLL_NAME]
        message.vote_option = cf.captures[_Tok.POLL_OPTION]
        message.hidden_vote_count = int(cf.captures[_Tok.NUMBER])
        return message

    if cf.match([_Tok.SENDER_ALIAS,
                 ' removed (?:your |his |her |their )?vote for "',
                 _Tok.POLL_OPTION, '" in the poll: ', _Tok.POLL_NAME]):
        message = cf.make_common(msg.PollRemoveVoteMessage)
        message.poll_name = cf.captures[_Tok.POLL_NAME]
        message.vote_option = cf.captures[_Tok.POLL_OPTION]
        message.hidden_vote_count = 0
        return message

    return None


@_register_rule()
def _match_poll_change_vote_message(cf: '_ChatFactory'
                                    ) -> Optional[msg.PollChangeVoteMessage]:
    if cf.match([_Tok.SENDER_ALIAS,
                 ' changed (?:your |his |her |their )?vote to "',
                 _Tok.POLL_OPTION, ' in the poll: ', _Tok.POLL_NAME]):
        message = cf.make_common(msg.PollChangeVoteMessage)
        message.poll_name = cf.captures[_Tok.POLL_NAME]
        message.vote_option = cf.captures[_Tok.POLL_OPTION]
        return message

    return None


@_register_rule()
def _match_poll_expired_message(cf: '_ChatFactory'
                                ) -> Optional[msg.PollExpiredMessage]:
    if cf.match([r'This poll is no longer available\.']):
        message = cf.make_common(msg.PollExpiredMessage)
        return message

    return None


@_register_rule()
def _match_admin_add_message(cf: '_ChatFactory'
                             ) -> Optional[msg.AdminAddMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' added ', _Tok.PARTICIPANT_NAME,
                 r' as a group admin\.']):
        message = cf.make_common(msg.AdminAddMessage)
        message.instigator = message.sender
        message.subject = cf.participant_manager.request_participant(
            cf.captures[_Tok.PARTICIPANT_NAME])
        return message

    return None


@_register_rule()
def _match_admin_remove_message(cf: '_ChatFactory'
                                ) -> Optional[msg.AdminRemoveMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' removed ', _Tok.PARTICIPANT_NAME,
                 r' as a group admin\.']):
        message = cf.make_common(msg.AdminRemoveMessage)
        message.instigator = message.sender
        message.subject = cf.participant_manager.request_participant(
            cf.captures[_Tok.PARTICIPANT_NAME])
        return message

    return None


@_register_rule()
def _match_app_new_score_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.AppNewScoreMessage]:
    if cf.match([_Tok.SENDER_ALIAS, '(?: just)? scored ', _Tok.APP_SCORE,
                 ' (?:point |points )?(?:in|playing) ', _Tok.APP_NAME]):
        message = cf.make_common(msg.AppNewScoreMessage)
        message.app_name = cf.captures[_Tok.APP_NAME]
        message.score = cf.captures[_Tok.APP_SCORE]
        message.personal_best = False
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' set a new personal best of ',
                 _Tok.APP_SCORE, ' (?:point |points )?(?:in|playing) ',
                 _Tok.APP_NAME]):
        message = cf.make_common(msg.AppNewScoreMessage)
        message.app_name = cf.captures[_Tok.APP_NAME]
        message.score = cf.captures[_Tok.APP_SCORE]
        message.personal_best = True
        return message

    return None


@_register_rule()
def _match_app_leaderboard_reshuffle_message(
        cf: '_ChatFactory') -> Optional[msg.AppLeaderboardReshuffleMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' moved up the leaderboard in ',
                 _Tok.APP_NAME]):
        message = cf.make_common(msg.AppLeaderboardReshuffleMessage)
        message.app_name = cf.captures[_Tok.APP_NAME]
        message.now_in_first_place = False
        return message

    if cf.match([_Tok.SENDER_ALIAS, ' is now in first place in ', _Tok.APP_NAME
                 ]):
        message = cf.make_common(msg.AppLeaderboardReshuffleMessage)
        message.app_name = cf.captures[_Tok.APP_NAME]
        message.now_in_first_place = True
        return message

    return None


@_register_rule()
def _match_app_challenge_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.AppChallengeMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' challenged you in ', _Tok.APP_NAME]):
        message = cf.make_common(msg.AppChallengeMessage)
        message.app_name = cf.captures[_Tok.APP_NAME]
        return message

    return None


@_register_rule()
def _match_text_message(cf: '_ChatFactory'
                        ) -> Optional[msg.TextMessage]:
    message = cf.make_common(msg.TextMessage)
    return message


@_register_rule()
def _match_subscribe_message(cf: '_ChatFactory'
                             ) -> Optional[msg.SubscribeMessage]:
    message = cf.make_common(msg.SubscribeMessage)
    message.inviter = message.sender
    message.invitees = [cf.participant_manager.request_participant(
        user_json['name']) for user_json in cf.message_json['users']]

    return message


@_register_rule()
def _match_unsubscribe_message(cf: '_ChatFactory'
                               ) -> Optional[msg.UnsubscribeMessage]:
    if cf.match([_Tok.PARTICIPANT_NAME, r' left the group\.']):
        message = cf.make_common(msg.UnsubscribeMessage)
        message.removed_self = True
        message.removalist = message.sender
        message.removed = message.sender
        return message

    message = cf.make_common(msg.UnsubscribeMessage)
    message.removed_self = False
    message.removalist = message.sender
    if cf.message_json['users'] == []:
        message.removed = cf.participant_manager.request_unknown_participant()
    else:
        message.removed = cf.participant_manager.request_participant(
            cf.message_json['users'][0]['name'])

    return message


@_register_rule()
def _match_wave_message(cf: '_ChatFactory'
                        ) -> Optional[msg.WaveMessage]:
    if cf.match([_Tok.PARTICIPANT_FIRST_NAME, r' waved hello to the group\.']):
        message = cf.make_common(msg.WaveMessage)
        return message

    return None


@_register_rule()
def _match_link_message(cf: '_ChatFactory'
                        ) -> Optional[msg.LinkMessage]:
    message = cf.make_common(msg.LinkMessage)
    if 'share' in cf.message_json:
        message.shared_link = cf.message_json['share'].get('shared_link')
    else:
        message.shared_link = None

    return message
