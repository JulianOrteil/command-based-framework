import weakref
from typing import Mapping, Optional, Set

from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.exceptions import SchedulerExistsError
from command_based_framework.subsystems import Subsystem


class SchedulerMeta(type):
    """Meta attributes for :py:class:`~command_based_framework.scheduler.Scheduler`.

    All methods and attributes here exist in :py:class:`~command_based_framework.scheduler.Scheduler`.
    """  # noqa: E501

    _instance: Optional[weakref.ReferenceType["Scheduler"]]

    @property
    def instance(cls) -> Optional["Scheduler"]:
        """The class-level instance attribute.

        Ensures that no more than one scheduler instance exists else
        undefined behavior regarding subsystems may occur.

        :return: The :py:class:`~command_based_framework.scheduler.Scheduler`
            instance if set, otherwise `None`.

        :raise SchedulerExistsError:
            An attempt was made to create multiple :py:class:`~command_based_framework.scheduler.Scheduler`
            instances.
        """  # noqa: E501
        if cls._instance is None:
            return None

        return cls._instance()

    @instance.setter
    def instance(cls, instance: "Scheduler") -> None:
        # Verify no previous instance exists
        if Scheduler.instance:
            raise SchedulerExistsError(
                "a scheduler already exists, a new one cannot be created",
            )
        cls._instance = weakref.ref(instance)


class Scheduler(object, metaclass=SchedulerMeta):
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

    _instance: Optional[weakref.ReferenceType["Scheduler"]] = None

    # All stack has references to all commands in any stack, regardless
    # of status
    _all_stack: Set[Command]

    # Action stack has references to the mappings between commands and
    # actions
    _actions_stack: Set[Mapping[Action, Mapping[Condition, Command]]]

    # Incoming stack has references to all commands that were just
    # scheduled
    _incoming_stack: Set[Command]

    # Scheduled stack has references to all commands that are normally
    # executing
    _scheduled_stack: Set[Command]

    # Interrupted stack has references to all commands that need to be
    # interrupted
    _interrupted_stack: Set[Command]

    # Ended stack has references to all commands that need to be ended
    # normally
    _ended_stack: Set[Command]

    # Subsystem stack has references to all subsystems that need to
    # have their periodic methods called
    _subsystem_stack: Set[Subsystem]

    def __init__(self) -> None:
        """Creates a new :py:class:`~command_based_framework.scheduler.Scheduler` instance."""
        Scheduler.instance = self
        self._reset_all_stacks()

    def bind_command(
        self,
        action: Action,
        command: Command,
        condition: Condition,
    ) -> None:
        """Bind `command` to an `action` to be scheduled on `condition`."""

    def cancel(self, *commands: Command) -> None:
        """Immediately cancel and interrupt any number of commands.

        If `commands` is not provided, interrupt all scheduled and
        incoming commands. The `interrupt` parameter of the
        :py:meth:`~command_based_framework.commands.Command.end` method
        for each command will be `True`.

        :param commands: Variable length of commands to cancel. If not
            provided, interrupt all active commands.
        :type commands: tuple
        """
        commands = commands or self._all_stack
        for command in commands:
            command.end(interrupted=True)
        self._reset_all_stacks()

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
        self._subsystem_stack.add(subsystem)

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

    def _reset_all_stacks(self) -> None:
        self._all_stack = set()
        self._actions_stack = set()
        self._incoming_stack = set()
        self._scheduled_stack = set()
        self._interrupted_stack = set()
        self._ended_stack = set()
        self._subsystem_stack = set()

    def _update_stack(self) -> None:
        pass
