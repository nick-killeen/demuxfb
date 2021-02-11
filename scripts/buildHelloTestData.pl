#!/usr/bin/perl
# Build data/chats/hello test data -- a simple conversation spanning multiple
# files intended to test ChatFeed construction from the disk.

use strict;
use warnings;

my $HELLO_PATH = "test/data/chats/hello";
my $NUM_FILES = 23;

if (-e $HELLO_PATH) {
    die "'hello' folder already exists, remove it before building new data";
}

mkdir $HELLO_PATH;
my $messageNum = 0;
for my $i (reverse 1..$NUM_FILES) {
    my $time1 = 1566296940000 + $messageNum * 1000;
    my $sender1 = ($i % 2) ? "Daniel" : "Henry";
    my $content1 = "$messageNum: Hello";
    ++$messageNum;

    my $time2 = 1566296940000 + $messageNum * 1000 + 500;
    my $sender2 = ($i % 2) ? "Henry" : "Daniel";
    my $content2 = "$messageNum: Hi";
    ++$messageNum;

    my $json = qq({
    "participants": [
        {
            "name": "Daniel"
        },
        {
            "name": "Henry"
        }
    ],
    "messages": [
        {
            "sender_name": "$sender2",
            "timestamp_ms": $time2,
            "content": "$content2",
            "type": "Generic"
        },
        {
            "sender_name": "$sender1",
            "timestamp_ms": $time1,
            "content": "$content1",
            "type": "Generic"
        }
    ],
    "title": "Daniel",
    "is_still_participant": true,
    "thread_type": "Regular",
    "thread_path": "inbox/Daniel_blah"
});
    open(my $fh, ">", "$HELLO_PATH/message_$i.json") or die;
	print $fh $json;
    close $fh;
}