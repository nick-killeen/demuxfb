"""
Script that does TODO
"""

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
    if isinstance(message, demuxfb.message.TextMessage):
        height += 1
print(height)
