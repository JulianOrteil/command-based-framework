from abc import abstractmethod
from enum import Enum, auto

# fmt: off
from command_based_framework._common import CallableCommandType, CommandType, ContextManagerMixin
from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler

# fmt: on


class Condition(Enum):
    """Enums representing different action conditions."""

    cancel_when_activated = auto()
    toggle_when_activated = auto()
    when_activated = auto()
    when_deactivated = auto()
    when_held = auto()


class Action(ContextManagerMixin):  # noqa: WPS214
    """Schedules :class:`~command_based_framework.commands.Command` based on a condition being met.

    Actions determine when commands are scheduled/executed. To do this,
    the scheduler periodically runs the :meth:`~.Action.poll`
    method. Any arbitrary condition, or multiple conditions, can be
    implemented in :meth:`~Action.poll`.

    To setup when commands are scheduled, bind them using any of the
    `when` methods. Attempts to bind a command multiple times in the
    same action will result in the previous binding being overridden.

    A command can be bound to a single or multiple actions.
    """  # noqa: E501

    # Flag to indicate the state of the action the last time it was
    # checked
    _last_state: bool

    def __init__(self) -> None:
        """Creates a new `Action` instance."""
        super().__init__()
        self._last_state = False

    @property
    def last_state(self) -> bool:
        """The state of the action the last time it was checked."""
        return self._last_state

    @last_state.setter
    def last_state(self, state: bool) -> None:
        self._last_state = state

    @abstractmethod
    def poll(self) -> bool:
        """Check if the condition to activate commands are met.

        Returns:
            `True` when all conditions are met for this action
            to activate and bound commands should be scheduled.
        """
        return False  # pragma: no cover

    def cancel_when_activated(self, command: CommandType) -> None:
        """Cancel `command` when this action is activated.

        Args:
            command: A :class:`~command_based_framework.commands.Command`
                or :class:`~command_based_framework.commands.CommandGroup`.
        """
        Scheduler.get_instance().bind_command(  # type: ignore
            self,
            command,
            Condition.cancel_when_activated,
        )

    def toggle_when_activated(self, command: Command) -> None:
        """Toggle scheduling `command` when this action is activated.

        For example, a button is pressed for the first time and a
        command runs. The same button is pressed again, but the command
        exits. The cycle repeats when the button is pressed for a third
        time.

        Args:
            command: A
                :class:`~command_based_framework.commands.Command`
                or
                :class:`~command_based_framework.commands.CommandGroup`.
        """
        Scheduler.get_instance().bind_command(  # type: ignore
            self,
            command,
            Condition.toggle_when_activated,
        )

    def when_activated(self, command: CallableCommandType) -> None:
        """Schedule `command` when this action is activated.

        Args:
            command: A
                :class:`~command_based_framework.commands.Command`,
                :class:`~command_based_framework.commands.CommandGroup`,
                or callable which returns one of the former.
        """
        Scheduler.get_instance().bind_command(  # type: ignore
            self,
            command,
            Condition.when_activated,
        )

    def when_deactivated(self, command: CallableCommandType) -> None:
        """Schedule `command` when this action is deactivated.

        Args:
            command: A
                :class:`~command_based_framework.commands.Command`,
                :class:`~command_based_framework.commands.CommandGroup`,
                or callable which returns one of the former.
        """
        Scheduler.get_instance().bind_command(  # type: ignore
            self,
            command,
            Condition.when_deactivated,
        )

    def when_held(self, command: CallableCommandType) -> None:
        """Schedule `command` when this action is perpetually activated.

        Args:
            command: A
                :class:`~command_based_framework.commands.Command`,
                :class:`~command_based_framework.commands.CommandGroup`,
                or callable which returns one of the former.
        """
        Scheduler.get_instance().bind_command(  # type: ignore
            self,
            command,
            Condition.when_held,
        )
