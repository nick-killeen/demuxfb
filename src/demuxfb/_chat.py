"""Contains the top-level logic of Chat construction."""

__all__ = ['Chat', 'build_chat']

from typing import List, Set, Dict, Optional, Sequence, Type
from inspect import currentframe


from .message import Message
from ._participant import Participant, _ParticipantManager
from ._progress_reporter import ProgressReporter
from ._chat_feed import ChatFeed
from ._tokens import _TokenMatcher, _Token, _Captures
from ._rules import _Ruleset, _all_rules
from ._reaction import Reaction


class Chat:
    """
    A detailed object representing a Facebook conversation.

    Attributes
    ----------
    messages: List[demuxfb.message.Message]
        Messages in the conversation, ordered by the time they were sent
        (earliest first).
    participants: Set[demuxfb.Participant]
        Participants in the conversation.
    """
    messages: List[Message]
    participants: Set[Participant]
    _participant_dict: Dict[str, Participant]
    _unknown_participant: Optional[Participant]

    def __init__(self) -> None:
        """
        This method should not be called publicly. Use `demxufb.build_chat`
        instead to create `Chat`s.
        """
        pass

    def _load_participants(self, participant_manager: _ParticipantManager
                           ) -> None:
        """
        Load participants from a complete _ParticipantManager object. Has
        the side-effect of 'requesting' unknown participant from the manager.
        """
        self.participants = participant_manager.get_participants()
        self._unknown_participant = \
            participant_manager.request_unknown_participant()

        self._participant_dict = {}
        for participant in self.participants:
            if participant != self._unknown_participant:
                self._participant_dict[participant.get_name()] = participant

    def get_participant(self, name: str) -> Optional[Participant]:
        """
        Get the `demuxfb.Participant` object uniquely identifying the
        given chat-member.

        Parameters
        ----------
        name: str
            The exact(case-sensitive) Facebook account name of the chat-member
            to get, as captured at the time of the archive snapshot.

        Returns
        -------
        demuxfb.Participant or None
            The participant corresponding to `name`, or `None` if no such
            participant was active in the chat.

        See Also
        --------
        demuxfb.Chat.get_unknown_participant
        """
        return self._participant_dict.get(name)

    def get_unknown_participant(self) -> Participant:
        """
        Get the unique (within the chat) `demuxfb.Participant` object that
        identifies all 'anonymous' chat members -- those who have blocked you,
        deleted their accounts, or whose name is otherwise missing under certain
        contexts.

        Even if a participant has a valid named identity, some of their
        involvements may be attributed to this unknown persona where Facebook
        fails to be explicit about their identity.

        Note: though there may be multiple distinct unidentifiable people in
        a conversation, they are all characterized by the one object this
        function returns.

        Returns
        -------
        demuxfb.Participant
            The unique (within the chat) object characterizing cases where a
            named participant identity is not present.

        See Also
        --------
        demuxfb.Chat.get_participant
        """
        return self._unknown_participant


class _State:
    """
    Container for state that is managed purely by rule logic, not being convoled
    in any internal process.
    """
    call_is_active = False
    plan_is_active = False


class _ChatFactory:
    """
    Manages state throughout the creation of messages, and orchestrates the
    initialization of `Chat` and therein `Message` objects.

    This class is permitted to access private members of the `Chat` class.
    """
    captures: Optional[_Captures]  # Captures from last successful match.
    message_json: Optional[dict]  # message_json currently being processed.
    ruleset: _Ruleset
    participant_manager: _ParticipantManager
    token_matcher: _TokenMatcher
    state: _State

    def __init__(self, feed: ChatFeed, owner_name: str) -> None:
        self._feed = feed
        self.ruleset = _Ruleset(_all_rules)
        self.participant_manager = _ParticipantManager(owner_name)
        self.token_matcher = _TokenMatcher()
        self.state = _State()

    # This function takes on what would otherwise be the role of a proper
    # Message.__init__ implementation. It is placed here rather than there so
    # that we don't have to weave the _ChatFactory instance through constructor
    # calls -- so that the `demuxfb.message` and `demuxfb._rules` (both where
    # eyeballs may be more numerous) look tidier and more integrous.
    def make_common(self, cls: Type[Message]) -> Message:
        """
        Create an instance of `cls` (subtype of `Message`), and populate its
        base `Message` fields with values from the the current `message_json`
        member.
        """
        message = cls()
        message.timestamp = self.message_json['timestamp_ms']
        message.content = self.message_json.get('content')
        message.sender = self.participant_manager.request_participant(
            self.message_json['sender_name'])
        message.message_json = self.message_json
        message.reactions = []

        for reaction_json in self.message_json.get('reactions') or []:
            reaction_sender = reaction_json['actor']
            reaction_emoji = reaction_json['reaction']
            reaction = Reaction(reaction_sender, reaction_emoji)
            message.reactions.append(reaction)

        return message

    def type_matches(self, message_type: str) -> bool:
        """
        Return true if the current `message_json` member has the specified json
        `'type'` field.
        """
        return self.message_json['type'] == message_type

    def match(self, against: Sequence[_Token]) -> bool:
        """
        Return true if the current `message_json` member's content matches the
        provided sequence of tokens. In addition, if the match is successful,
        the `captures` instance member is set to represent the captures from the
        match.

        Note
        ----
        This method MUST NOT have calls with two semantically distinct values of
        `against` made at the same line number. That is, globally to this
        _ChatFactory instance, the line number of calls to this method must
        uniquely identify `against`, regardless of source file.
        """
        caller_line_num = currentframe().f_back.f_lineno
        captures = self.token_matcher.match(against,
                                            self.message_json['content'],
                                            cache_id=caller_line_num)
        if captures is None:
            return False

        self.captures = captures
        return True

    def build(self, progress_reporter: Optional[ProgressReporter]) -> Chat:
        """
        Create the `Chat` object from the factory, logging progress to
        `progress_reporter`.
        """
        # _ChatFactory needs friendly access to Chat.
        # pylint: disable=protected-access

        if progress_reporter is not None:
            progress_reporter.start()

        chat = Chat()
        chat.messages = []
        chat.participants = set()

        for message_json in self._feed.message_json_iter():
            self.message_json = message_json
            message = self.ruleset.apply(self)
            chat.messages.append(message)

            if progress_reporter is not None:
                progress_reporter.finish_message(message)

        chat._load_participants(self.participant_manager)

        if progress_reporter is not None:
            progress_reporter.finish()

        return chat


def build_chat(
        feed: ChatFeed,
        owner_name: str,
        progress_reporter: Optional[ProgressReporter] = None) -> Chat:
    """
    Build a detailed chat object from an archive.

    Parameters
    ----------
    feed: demuxfb.ChatFeed
        The feed defining the source that the json conversation data is to be
        read from.
    owner_name: str
        The Facebook account name of the person who downloaded the Facebook
        archive. This is needed so the builder knows which participant 'you'
        refers to.
    progress_reporter: demuxfb.ProgressReporter, optional
        Used to report progress in the process of building the chat. If
        unspecified, no reporting will take place.

    Returns
    -------
    demuxfb.Chat
        A detailed object representing the chat read from the specified feed.

    Raises
    ------
    NoMatchingRuleException
        When no enabled message-matching rule in the ruleset matches a json
        element of the feed.
    """
    chat_factory = _ChatFactory(feed, owner_name)
    chat = chat_factory.build(progress_reporter)

    return chat
