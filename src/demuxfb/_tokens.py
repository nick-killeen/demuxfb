"""
Module defining 'tokens' and their associated methods. Tokens are used to define
the string matching rules for message generation.
"""
from typing import Union, Sequence, Optional, Dict, List, Pattern, Type, Set, DefaultDict
from collections import defaultdict
from enum import Enum, auto
import re


class _Tok(Enum):
    """Special Token names that appear in message matching rules."""
    PARTICIPANT_NAME = auto()
    SENDER_ALIAS = auto()
    PARTICIPANT_FIRST_NAME = auto()
    ANYTHING = auto()
    PLAN_DATE_TIME = auto()
    PLAN_TITLE = auto()
    PLAN_TIME = auto()
    POLL_NAME = auto()
    POLL_OPTION = auto()
    NUMBER = auto()
    EMOJI = auto()
    APP_NAME = auto()
    APP_SCORE = auto()


_initial_token_patterns = {
    _Tok.PARTICIPANT_NAME: '(.*)',
    _Tok.SENDER_ALIAS: '(.*)',
    _Tok.PARTICIPANT_FIRST_NAME: '(.*)',
    _Tok.ANYTHING: '(.*)',
    _Tok.PLAN_DATE_TIME: '(.*)',
    _Tok.PLAN_TITLE: '(.*)',
    _Tok.PLAN_TIME: r'(\d{1,2} (?:AM|PM))',
    _Tok.POLL_NAME: '(.*)',
    _Tok.POLL_OPTION: '(.*)',
    _Tok.NUMBER: r'(\d+)',
    _Tok.EMOJI: '(.*)',
    _Tok.APP_NAME: '(.*)',
    _Tok.APP_SCORE: '(.*)'
}

# This union saves us some visual noise for literals where the matching rules
# are specified (in _rules.py).
_Token = Union[_Tok, str]

# This union is so that if `captures: _Captures` makes one match on the token
# _Tok.X, then it can be accessed with the brief `captures[_Tok.X]`, while in
# case of multiple captures, they are still indexed explicitly with
# `captures[_Tok.X][0]`, `captures[_Tok.X][1]`, ... again, hopefully tidying up
# _rules.py.
_Captures = Dict[Type[_Tok], Union[str, List[str]]]


class _TokenMatcher:
    """
    _TokenMatcher objects track the state of token definitions, and are used to
    apply 'matching' tests between sequences of these tokens and strings
    (message content).

    Note
    ----
    This class caches compiled patterns for a small speedup.
    """
    _token_patterns: Dict[_Tok, str]
    _cached_sequence_patterns: Dict[int, Pattern]
    _cache_sequence_dependency: DefaultDict[_Tok, Set[int]]

    def __init__(self) -> None:
        self._token_patterns = _initial_token_patterns
        self._cached_sequence_patterns = {}
        self._cache_sequence_dependency = defaultdict(set)

    def _compile_pattern(self, tokens: Sequence[_Token],
                         sequence_cache_id: Optional[int] = None) -> Pattern:
        # Check the cache first.
        if sequence_cache_id is not None:
            cached_compiled_pattern = self._cached_sequence_patterns.get(
                sequence_cache_id)
            if cached_compiled_pattern is not None:
                return cached_compiled_pattern

        # Compile the pattern, sanity-check the string literals, and keep track
        # of non-literals in an array `special_tokens`
        special_tokens = []
        pattern = '^'
        for token in tokens:
            if isinstance(token, _Tok):
                special_tokens.append(token)
                pattern += self._token_patterns[token]
            else:
                # Unescaped dots in literals are probably accidental typos --
                # they should be escaped in the source.
                if re.search(r'[^\\]\.', token) is not None:
                    raise Exception('Literal Token contains unescaped dot: '
                                    + str(token))
                # Capturing groups in literals violate contracts (see
                # `_TokenMatcher.match`).
                if re.search(r'\([^?]', token) is not None:
                    raise Exception('Literal Token contains capturing group: '
                                    + str(token))
                pattern += token
        pattern += '$'
        compiled_pattern = re.compile(pattern)

        # Cache the regex.
        if sequence_cache_id is not None:
            self._cached_sequence_patterns[sequence_cache_id] = compiled_pattern
            for special_token in special_tokens:
                self._cache_sequence_dependency[special_token].add(
                    sequence_cache_id)

        return compiled_pattern

    def update_token_pattern(self, token: _Tok, pattern: str) -> None:
        """
        Set or update the meaning of a token.

        Parameters
        ----------
        token: Tok
            Token to set the pattern for.
        pattern: str
            Regex pattern to set. It must contain exactly one capturing group.
        """
        self._token_patterns[token] = pattern

        for sequence_cache_id in self._cache_sequence_dependency.get(token
                                                                     ) or []:
            self._cached_sequence_patterns.pop(sequence_cache_id)

    def match(self, against: Sequence[_Token], string: str, cache_id: int
              ) -> Optional[_Captures]:
        """
        Match a string against a sequence of tokens.

        Facebook tends to insert a '.' at the end of automatically generated
        sentences, provided there was no terminal punctiation '?!.' already
        interpolated there. If there is a dot, we assume Facebook put it there,
        and it isn't part of the content. This will lead to some erroneous
        truncations. For instance, if someone sets their nickname to 'Don 2.0.',
        we will capture the nickname as 'Don 2.0' (missing a single period).

        So long as the second-last character is one of '?!.', then the capture
        will work losslessly even if the last character is a dot.

        Parameters
        ---------
        tokens : Sequence[_Token]
            Sequence of Tokens to match against. `str`-typed elements of this
            sequence must contain no capturing groups.
        string : int
            The string to match.
        cache_id : int
            Unique identifier for the value of `tokens`, to be used for regex
            compilation caching.

        Returns
        -------
        Captures, or None
            Object representing the special token captures from the match, or
            `None` if the match was not successful.
        """
        return self._match0(against, string, cache_id, False)

    def _match0(self, against: Sequence[_Token], string: str, cache_id: int,
                has_stripped_dot: bool) -> Optional[_Captures]:
        """See `_TokenMatcher.match`."""

        # Where the rule is such that Facebook may have inserted a '.', this
        # block first orchestrates one recursive call with the dot stripped.
        if isinstance(against[-1], _Tok) and not has_stripped_dot:
            ends_with_any_punctuation = re.search(r'[.!?]$', string) is not None
            if not ends_with_any_punctuation:
                # Messages ending with a Tok must always end in punctuation.
                return None

            ends_with_single_dot = re.search(r'[^.!?]\.$', string) is not None
            if ends_with_single_dot:
                dotless_captures = self._match0(against, string[:-1],
                                                cache_id, True)
                if dotless_captures is not None:
                    return dotless_captures

        pattern = self._compile_pattern(against, sequence_cache_id=cache_id)
        res = pattern.search(string)
        if not res:
            return None

        captures = {}
        groups = list(res.groups())

        for token in against:
            if isinstance(token, _Tok):
                capture = groups.pop(0)
                if token not in captures:
                    captures[token] = capture
                elif isinstance(captures[token], str):
                    captures[token] = [captures[token], capture]
                else:
                    captures[token].append(capture)
        return captures
