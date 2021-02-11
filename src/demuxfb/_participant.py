"""Module concerning participant identity management."""

from typing import Dict, Set


class Participant:
    """
    Identifies a chat participant.

    Two Participant objects represent the same person if and only if they are
    equivalent (they reference the same location in memory). All unattributable
    actions are said to be done by one 'unknown' persona.

    Note: object-equivalency does not hold across multiple chats.
    """
    _name: str
    _is_me: bool

    def __init__(self, name: str, is_me: bool = False) -> None:
        """
        This method should not be called publicly. Use
        `demuxfb.Chat.get_participant` or
        `demuxfb.Chat.get_anonymous_participant` instead to get instances.
        """
        self._name = name
        self._is_me = is_me

    def get_name(self) -> str:
        """
        Get this participant's Facebook account name.

        Returns
        -------
        str
            This partipant's Facebook account name. The value will be `'Facebook
            User'` if the participant is anonymous.
        """
        return self._name

    def is_me(self) -> bool:
        """
        Return true if this participant is the one who downloaded the Facebook
        archive.

        Returns
        -------
        bool
            True if this participant is the one who downloaded the Facebook
            archive.
        """
        return self._is_me


class _ParticipantManager:
    """
    Responsible for building and retrieving unique `Participant` objects during
    the creation of a `Chat`.
    """
    _me: Participant
    _unknown_participant: Participant
    _participants: Dict[str, Participant]

    def __init__(self, my_name: str) -> None:
        self._me = Participant(my_name, is_me=True)
        self._unknown_participant = Participant('Facebook User')
        self._participants = {}

    def _has_requested_before(self, name: str) -> bool:
        return name in self._participants

    # We log requests for identity objects so that, say, if there are no
    # unattributable actions in a chat, then the 'unknown participant' object is
    # not yielded as a chat participant.
    def request_participant(self, name: str) -> Participant:
        # These values may have been interpolated by the Facebook exporter in
        # place of account names or nicknames.
        unknown_names = ['Facebook User', 'a participant',
                         'A participant', 'a contact', 'A contact', '']

        # Maintain that every name we encounter is given a unique Participant
        # object stored in the self._participants dict.
        # If we encounter an anonymous participant, all potential name-keys are
        # inserted to point to the one Participant object.
        if not self._has_requested_before(name):
            if name == self._me.get_name():
                self._participants[name] = self._me
            elif name in unknown_names:
                for unknown_name in unknown_names:
                    self._participants[unknown_name] = self._unknown_participant
            else:
                self._participants[name] = Participant(name)

        return self._participants[name]

    def request_unknown_participant(self) -> Participant:
        return self.request_participant(self._unknown_participant.get_name())

    def request_me(self) -> Participant:
        return self.request_participant(self._me.get_name())

    def get_participants(self) -> Set[Participant]:
        return set(self._participants.values())
