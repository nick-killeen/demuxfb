from pathlib import Path

import sys
sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position

chat = demuxfb.build_chat(
    demuxfb.ChatFolderFeed(Path('C:/Users/nicho/Desktop/fresh')),
    'Nicholas Killeen',
    demuxfb.IntervalProgressReporter()
)
height = 0
for message in chat.messages:
    if isinstance(message, demuxfb.message.TextMessage) or isinstance(message, demuxfb.message.UnrecognizedMessage):
        for participant in chat.participants:
            if message.content.startswith(participant.get_name() + " "):
                print("Sus:", message.content)


print(height)
