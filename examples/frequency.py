from pathlib import Path

import sys
sys.path.append('src/')
import demuxfb  # nopep8 pylint: disable=wrong-import-position

chat = demuxfb.build_chat(
    demuxfb.ChatFolderFeed(Path('C:/Users/nicho/Desktop/fresh')),
    'Nicholas Killeen',
    demuxfb.IntervalProgressReporter()
)


message_types = [ty for ty in demuxfb.message.__all__ if ty.endswith(
    'Message') and ty != 'Message']
message_type_count = dict.fromkeys(message_types, 0)

for participant in chat.participants:
    print(participant.get_name())

for message in chat.messages:
    message_type_count[str(type(message)).split('.')[-1].split("'")[0]] += 1

for message_type in sorted(message_type_count):
    print(message_type + ': ' + str(message_type_count[message_type]))
