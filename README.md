# demuxfb - demultiplex exported facebook json chat data!
demuxfb is a Python package to reframe conversations from Facebook 'Download
Your Information' json dumps into a more exact form, accounting for the
different categorizations of messages that the json metadata itself does not
distinguish.

## Motivation
Facebook chats are very feature-rich. All within a chat, there may be polls,
events, video and audio calls, embedded games, and more. But the Facebook
'Download Your Data' exportation format fails to reflect these features; many
distinct categories of messages are structurally indistinguishable from
ordinary text messages.

When analysing the dataset, should an automated event reminder, 'Reminder, 30
minutes until 10 PM.', be treated the same as a human-written message? This
should be up to the analyst to decide, not the exportation format.

## Scope
This package defines a method to 'parse' Facebook JSON data for single chats
into a more useful and complete representative form. This form is intended to
be used an intermediary for analysis on the dataset.

We achieve this by string-matching message content to known schemas for the
special feature-driven messages. The JSON messages in the original time series
are promoted into appropriate Python classes according to these rules.

This process is limited in several ways.
- It is difficult to establish a formal spec of what these schemas are -- we are
  on the outside, so it has been up to human inference on a limited dataset. So,
  given this difficulty in verification, the rules may be wrong or incomplete in
  the first place, or may silently become obsolete in future Facebook updates.
- Facebook features are region-specific. Currently, this package assumes an
  Australian dataset, so the inbuilt rules will fail to detect things like
  sending money through messenger (a U.S. feature).
- The Facebook exporter compresses the natural data. For example, Alice typing
  'Alice waved hello to the group.' is impossible to distinguish from Alice
  using the wave feature. We take a parsimonious approach in these kinds of
  situations where there is no single correct answer, even though different
  or more complex procedures may emperically be better in the relevant context.

Expect misclassification.

## Installation
The recommended approach is to copy the src/demuxfb folder to wherever you're
using it, and just put `import demuxfb` as with any other source package. This
allows you to easily modify the source to suit your exact needs, if necessary
(see the [Modification section](#modification)).

Alternatively, if it suits your current needs as is, you can install the package
locally by cloning the repository and typing

```
pip install dist/demuxfb-VER.tar.gz
```

where `VER` points to a valid version in the `dist/` folder (e.g. `2020.12.15`,
representing the version that was developed against a Facebook archive generated
at that date).

TODO Python version!

## Usage
You can download your Facebook data at https://www.facebook.com/dyi/. Before
beginning the download, you must set the file format to 'JSON' and confirm
that the 'Messages' option is checked.

Once the archive has been generated and you have downloaded it, unzip it.
Your chats should then be located in the `messages/inbox/` and
`messages/archived_threads/` subfolders. From here, a simple usage example would
be as follows.

```python
from pathlib import Path
import demuxfb

# 1. Point to where the conversation will be fed in from the disk.
path = Path('C:/users/nicho/downloads/facebook-nicholaskilleen/'
            'messages/inbox/ourchat_95kldfjg4')
feed = demuxfb.ChatFolderFeed(path)

# 2. Create the chat (takes a while, reports progress to stdout).
chat = demuxfb.build_chat(feed, 'Nicholas Killeen')

# 3. Do some stub analysis with it.
print('Number of text messages in the conversation:',
      len([message for message in chat.messages
           if isinstance(message, demuxfb.message.TextMessage)]))
```
## Documentation
The documentation is available online at https://nick-killeen.github.io/demuxfb/.
You can also read it in source or with `help(demuxfb)` in Python, or can compile
it with Sphinx by using the Makefile in the `docs/` directory.

## Modification
You may want to extend or modify demuxfb's vocabulary to work better with your
dataset. This is not possible to do through the package interface, so you will
need to modify the source. This section can help get you started.

demuxfb works by iterating through all JSON messages, for each consulting an
ordered list of rules until one of them 'matches' the current JSON iterate and
produces an appropriate message object. It is these rules that define the
parsing logic, so they will generally be the focus of any modifications or
additions you would like to make.

All rules are defined in the `src/demuxfb/_rules.py` file. For example, consider 
the scenario of wanting to recognize JSON snippets similar to the following as
`PlanDeletionMessages`:

```json
{
  "sender_name": "Jacob Smith",
  "timestamp_ms": 1478855024210,
  "content": "Jake deleted the plan Saturday Hangout for Sat, Aug 5 at 12 PM.",
  "type": "Generic"
}
```

Then, in the `src/demuxfb/_rules.py` file, we might have the following rule:

```python
@_register_rule()
def _match_plan_deletion_message(cf: '_ChatFactory'
                                 ) -> Optional[msg.PlanDeletionMessage]:
    if cf.match([_Tok.SENDER_ALIAS, ' deleted the plan ', _Tok.PLAN_TITLE,
                 ' for ',  _Tok.PLAN_DATE_TIME]):
        message = cf.make_common(msg.PlanDeletionMessage)
        message.plan_title = cf.captures[_Tok.PLAN_TITLE]
        message.plan_date_time = cf.captures[_Tok.PLAN_DATE_TIME]
        return message
    
    return None
```

All rules are registered with the `@_register_rule` decorator. The order in which
these registrations appear in source will correspond to the precedence of rules,
more general rules being defined at the bottom of the file.

Rules have two possible return types: they return `None` to indicate their
non-applicability to the current state, causing demuxfb to move on to the next
rule; or they instantiate and return a specialized message object which will be
copied to the output structure (here `PlanDeletionMessage`). These types are
defined in the `src/demuxfb/message.py` file, where you are free to add your own
or change the existing ones.

Rules take in a single `_ChatFactory` argument that encompasses the world state.
This state persists throughout the sequential parsing process, and includes:
- A `message_json` property that contains the current JSON that is meant to be
  turned into a message.
- An identity manager for the participants in the conversation.
- Token definitions (which *can* be updated dynamically, though no rule
  currently makes use of this).
- Scoping variables, such as `plan_is_active` -- one might expect that a genuine
  plan deletion event will not occur if there does not exist an ongoing plan, so,
  we can set and unset this variable when we recognize plan deletion and
  creation events and use it accordingly (see the actual
  `_match_plan_deletion_message` in source for an example).

The relevant documentation for this starts at the definition of `_ChatFactory`
in the `src/demuixfb/_chat.py` file, but an explicit visit there is not
immediately necessary, since the existing rules in `src/demuxfb/_rules.py`
exemplify the repetitive use of small collection of patterns.