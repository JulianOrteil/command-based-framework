from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.subsystems import Subsystem


class Scheduler(object):
    """Schedules :py:class:`~command_based_framework.commands.Command` that control :py:class:`~command_based_framework.subsystems.Subsystem` when activated by :py:class:`~command_based_framework.actions.Action`.

    The scheduler handles events and resource management for the
    framework. A scheduler **must** exist **before** creating any
    commands, subsystems, or actions. Only one scheduler can exist in a
    program at any given time. More than one scheduler will result in
    undefined behavior.

    The scheduler has the following life-cycle:

    **1**: All actions with bound `when` methods have their :py:meth:`~command_based_framework.actions.Action.poll`
    methods called. For efficiency, unbound actions are ignored.

    **2**: If a `when` condition is met, the related command(s) are
    put onto the incoming stack. Any two commands which share
    requirements (subsystems) will result in the currently scheduled
    command being interrupted. Two newly scheduled commands with shared
    requirements will result in only one of the commands being scheduled
    and a warning being thrown about the conflict.

    **3**: Any subsystem not bound to a scheduled or incoming command
    will have their default command scheduled, if there is one.

    **4**: Commands scheduled for interruption are interrupted. Commands
    scheduled to exit because their :py:meth:`~command_based_framework.commands.Command.is_finished`
    returned `True`, are ended. Incoming commands are initialized. Note
    that commands initialized in one frame will not be normally executed
    until the next frame.

    **5**: Currently scheduled commands have their :py:meth:`~command_based_framework.commands.Command.is_finished`
    methods checked. If `True` is returned, the command(s) are scheduled
    for exit and their :py:meth:`~command_based_framework.commands.Command.execute`
    method is ignored. Otherwise, their :py:meth:`~command_based_framework.commands.Command.execute`
    method is called. Commands are allowed to raise errors from their
    :py:meth:`~command_based_framework.commands.Command.execute` methods
    and their :py:meth:`~command_based_framework.commands.Command.handle_exception`
    method will be called with the output from :py:meth:`sys.exec_info`.
    Return `True` to indicate the error is handled and normal execution
    can continue. Any other return will result in the command being
    immediately interrupted and de-stacked. A warning about the error
    will be thrown.

    **6**: The main stack updates with interrupted/finished commands
    taken off and initialized commands put on.

    **7**: This cycle repeats.

    **8**: Upon shutdown, all current commands are interrupted and
    de-stacked. The scheduler then exits its event loop.
    """  # noqa: E501

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

    def prestart_setup(self) -> None:
        """Run prestart checks and setup when :py:meth:`~command_based_framework.scheduler.Scheduler.execute` is called."""  # noqa: E501

    def register_subsystem(self, subsystem: Subsystem) -> None:
        """Continuously call a :py:meth:`~command_based_framework.subsystems.Subsystem.periodic` method regardless if the subsystem is bound to a scheduled command.

        :param subsystem: The subsystem who's :py:meth:`~command_based_framework.subsystems.Subsystem.periodic`
            method should be called at all times.
        :param subsystem: :py:class:`~command_based_framework.subsystems.Subsystem`
        """  # noqa: E501

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
