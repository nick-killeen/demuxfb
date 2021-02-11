"""Module for logic about reporting on the long progress of `Chat` creation."""


from abc import ABC, abstractmethod
from typing import Callable, Any
import datetime

from .message import Message


class ProgressReporter(ABC):
    """
    Interface for reporting on progress during the construction of a chat, which
    can take a while. This is an optional argument to `demuxfb.build_chat`.

    See Also
    --------
    demuxfb.IntervalProgressReporter
    """

    @abstractmethod
    def finish_message(self, message: Message) -> None:
        """
        Called when a message has finished being constructed.

        Parameters
        ----------
        message: demuxfb.mesage.Message
            The message that was just constructed.
        """
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """Called when Chat construction begins."""
        raise NotImplementedError

    @abstractmethod
    def finish(self) -> None:
        """Called when Chat construction finishes."""
        raise NotImplementedError


class IntervalProgressReporter(ProgressReporter):
    """
    ProgressReporter that logs time and number of messages processed at a
    regular interval.
    """
    _start_time: float
    _message_count: int
    _report_interval: float
    _report_function: Callable[[str], Any]

    def __init__(self, report_interval_seconds: float = 1.0,
                 report_function: Callable[[str], Any] = print) -> None:
        """
        Create reporter.

        Parameters
        ----------
        report_interval_seconds : float, defaults to 1.0
            Interval (in seconds) to report at.
        report_function : function, defaults to print
            Function that takes in a str and logs its value via some
            side-effect. This function will be used to make the reports.
        """
        self._message_count = 0
        self._next_report_time = 0.0
        self._report_interval = report_interval_seconds
        self._report_function = report_function

    def finish_message(self, message: Message) -> None:
        self._message_count += 1
        # Report our progress if we are due to.
        current_time = datetime.datetime.now().timestamp()
        if current_time >= self._next_report_time:
            self._next_report_time = current_time + self._report_interval
            self._report_function(
                'Messages processed: {}'.format(self._message_count))

    def start(self) -> None:
        self._start_time = datetime.datetime.now().timestamp()

    def finish(self) -> None:
        end_time = datetime.datetime.now().timestamp()
        d_time = end_time - self._start_time
        self._report_function('Processed {} messages\nTook: {} seconds'.format(
            self._message_count, d_time))
