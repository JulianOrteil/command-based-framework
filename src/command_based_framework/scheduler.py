from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.subsystems import Subsystem


class Scheduler(object):
    """Schedules :py:class:`~command_based_framework.commands.Command` when activated by :py:class:`~command_based_framework.actions.Action` that control :py:class:`~command_based_framework.subsystems.Subsystem`."""  # noqa: E501

    def bind_command(
        self,
        action: Action,
        command: Command,
        condition: Condition,
    ) -> None:
        """Bind `command` to an `action` to be scheduled on `condition`."""

    def cancel(self, *commands: Command) -> None:
        """Immediately cancel any number of commands.

        If `commands` is not provided, cancel all scheduled commands.
        """

    def execute(self) -> None:
        """Perpetually run the event loop."""

    def register_subsystem(self, subsystem: Subsystem) -> None:
        """Continuously call a :py:meth:`~command_based_framework.subsystems.Subsystem.periodic` method."""  # noqa: E501

    def run_once(self) -> None:
        """Run one complete loop of the scheduler's event loop."""

    def shutdown(self) -> None:
        """Shut the scheduler down.

        If :py:meth:`~command_based_framework.scheduler.Scheduler.execute`
        was called, calling this from the same thread will deadlock.
        """

    def _cancel_commands(self) -> None:
        pass

    def _execute_commands(self) -> None:
        pass

    def _execute_subsystems(self) -> None:
        pass

    def _init_commands(self) -> None:
        pass

    def _poll_action(self, action: Action) -> None:
        pass

    def _poll_actions(self) -> None:
        pass

    def _update_stack(self) -> None:
        pass
