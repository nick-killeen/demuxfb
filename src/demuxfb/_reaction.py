"""
Module to define the message `Reaction` class for the emoji responses people can
attach to messages.
"""

from ._participant import Participant


class Reaction:
    emoji: str
    sender: Participant

    def __init__(self, emoji: str, sender: Participant) -> None:
        """This method should not be called publicly."""
        self.emoji = emoji
        self.sender = sender
