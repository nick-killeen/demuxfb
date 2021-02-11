"""
demuxfb - parse Facebook conversation archives
==============================================
demuxfb is a Python package to reframe conversations from Facebook 'Download
Your Information' json dumps into a more exact form, accounting for the
different categorizations of messages that the json metadata itself does not
distinguish.

Github: https://github.com/nick-killeen/demuxfb

Warning on Misclassification
----------------------------
The exportation functionality Facebook provides is not one-to-one, so
reverse-engineering from the compressed form will inevitably result in some
misclassification errors. This package takes the route of parsimony rather than
trying to finesse the 'overclassifaction' and 'underclassifcation' margin with a
particular context in mind. Expect misclassification.

Functions
---------
`build_chat`
    Builds a `Chat` from a Facebook archive -- performs the package's task.

Modules
-------
`media`
    Defines media types used by `demuxfb.message.MediaMessage`.
`message`
    Defines the classification structure of messages.

Example
-------
This example demonstrates the orchestration of a call to `build_chat` and a
simple usage of the resultant `Chat` object.

    >>> from pathlib import Path
    >>> import demuxfb
    >>> path = Path('C:/users/nicho/downloads/facebook-nicholaskilleen/'
    ...             'messages/inbox/ourchat_95kldfjg4')
    >>> feed = demuxfb.ChatFolderFeed(path)
    >>> chat = demuxfb.build_chat(feed, 'Nicholas Killeen') # May take a while.
    >>> print('Number of text messages in the conversation:',
    ...       len([message for message in chat.messages
    ...            if isinstance(message, demuxfb.message.TextMessage)]))

"""
from ._chat import Chat, build_chat
from ._chat_feed import InvalidChatFeedException, ChatFeed, ChatFileFeed, ChatFolderFeed
from ._participant import Participant
from ._progress_reporter import ProgressReporter, IntervalProgressReporter
from ._reaction import Reaction

__all__ = [n for n in globals() if n[0] != '_']
