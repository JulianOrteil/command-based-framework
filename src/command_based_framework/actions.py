from abc import ABC, abstractmethod
from enum import Enum, auto

from command_based_framework.commands import Command


class Condition(Enum):
    """Enums representing different action conditions."""

    cancel_when_activated = auto()
    toggle_when_activated = auto()
    when_activated = auto()
    when_deactivated = auto()
    when_held = auto()


class Action(ABC):
    """Schedules :py:class:`~command_based_framework.commands.Command` based on a condition being met.

    Actions determine when commands are scheduled/executed. To do this,
    the scheduler periodically runs the :py:meth:`~command_based_framework.actions.Action.poll`
    method. Any arbitrary condition, or multiple conditions, can be
    implemented in :py:meth:`~command_based_framework.actions.Action.poll`.

    To setup when commands are scheduled, bind them using any of the
    `when` methods. Attempts to bind a command multiple times in the
    same action will result in the previous binding being replaced by
    the new one.

    A command can be bound to a single or multiple actions.
    """  # noqa: E501

    @abstractmethod
    def poll(self) -> bool:
        """Check if the condition to activate commands are met.

        Only return `True` when all conditions are met for this action
        to activate and schedule bound commands.
        """
        return False

    def cancel_when_activated(self, command: Command) -> None:
        """Cancel `command` when this action is activated."""

    def toggle_when_activated(self, command: Command) -> None:
        """Toggle scheduling `command` when this action is activated.

        For example, a button is pressed for the first time and a
        command runs. The same button is pressed again, but the command
        exits. The cycle repeats when the button is pressed for a third
        time.
        """

    def when_activated(self, command: Command) -> None:
        """Schedule `command` when this action is activated."""

    def when_held(self, command: Command) -> None:
        """Schedule `command` when this action is perpetually activated."""

    def when_deactivated(self, command: Command) -> None:
        """Schedule `command` when this action is deactivated."""
