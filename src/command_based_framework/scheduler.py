import sys
import warnings
import weakref
from concurrent.futures import Future
from contextlib import suppress
from typing import Dict, Optional, Set

if sys.version_info >= (3, 10):
    # WPS433: Found nested import
    # WPS440: Found block variables overlap
    from typing import TypeAlias  # pragma: no cover
else:
    # WPS433: Found nested import
    # WPS440: Found block variables overlap
    from typing_extensions import TypeAlias  # pragma: no cover

# Annotations only
with suppress(ImportError):
    from command_based_framework.actions import Action, Condition  # pragma: no cover
    from command_based_framework.commands import Command  # pragma: no cover
    from command_based_framework.subsystems import Subsystem  # pragma: no cover

from command_based_framework.exceptions import SchedulerExistsError

ConditionCommandType: TypeAlias = Dict["Condition", Set["Command"]]
ActionStack: TypeAlias = Dict["Action", ConditionCommandType]


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

    # Clock speed is how fast the scheduler runs per second
    _clock_speed: float

    # All stack has references to all commands in any stack, regardless
    # of status
    _all_stack: Set["Command"]

    # Action stack has references to the mappings between commands and
    # actions
    _actions_stack: ActionStack

    # Incoming stack has references to all commands that were just
    # scheduled
    _incoming_stack: Set["Command"]

    # Scheduled stack has references to all commands that are normally
    # executing
    _scheduled_stack: Set["Command"]

    # Ended stack has references to all commands that need to be ended
    # normally
    _ended_stack: Set["Command"]

    # Subsystem stack has references to all subsystems that need to
    # have their periodic methods called
    _subsystem_stack: Set["Subsystem"]

    def __init__(self) -> None:
        """Creates a new :py:class:`~command_based_framework.scheduler.Scheduler` instance."""
        Scheduler.instance = self
        self.clock_speed = 1 / 60
        self._reset_all_stacks()

    @property
    def clock_speed(self) -> float:
        """How many times the scheduler will attempt to run per second.

        Because the scheduler is synchronous, long-running commands may
        degrade the ability for the scheduler to stick to this rate.
        This value must always remain above 0 otherwise the CPU may be
        deadlocked.

        Defaults to 60 ticks per second.

        :raise ValueError: An attempt to set the clock speed at or below
            0 was made.
        """
        return self._clock_speed

    @clock_speed.setter
    def clock_speed(self, clock_speed: float) -> None:
        # Ensure the new speed is above 0
        if clock_speed <= 0:
            raise ValueError("clock speed must be at or above 0")

        self._clock_speed = clock_speed

    def bind_command(
        self,
        action: "Action",
        command: "Command",
        condition: "Condition",
    ) -> None:
        """Bind `command` to `action` to be scheduled on `condition`."""
        current_condition_stack = self._actions_stack.setdefault(
            action,
            {condition: {command}},
        )
        for cond, cmdlist in current_condition_stack.items():
            for cmd in cmdlist.copy():
                if cmd == command:
                    cmdlist.remove(cmd)
                    break
            current_condition_stack[cond] = cmdlist
        current_condition_stack.setdefault(condition, set()).add(command)
        self._actions_stack[action] = current_condition_stack
        self._all_stack.add(command)

    def cancel(self, *commands: "Command") -> None:  # noqa: WPS213
        """Immediately cancel and interrupt any number of commands.

        If `commands` is not provided, interrupt all scheduled and
        incoming commands. The `interrupt` parameter of the
        :py:meth:`~command_based_framework.commands.Command.end` method
        for each command will be `True`.

        :param commands: Variable length of commands to cancel. If not
            provided, interrupt all active commands.
        :type commands: tuple
        """
        cancel_all = not commands
        all_commands = set(commands) or self._all_stack
        for command in all_commands.copy():
            try:
                command.end(interrupted=True)
            except Exception:
                command.handle_exception(*sys.exc_info())
                warnings.warn(
                    (
                        "{name} failed to interrupt, this command may have "
                        "failed to properly quit."
                    ).format(name=command.name),
                    RuntimeWarning,
                )

                # Reset the interrupt flag
                command.needs_interrupt  # noqa: WPS428

            # Reset all requirements' current commands to none
            for requirement in command.requirements:
                requirement.current_command = None

            # Remove the command from all stacks
            with suppress(KeyError):
                self._all_stack.remove(command)
            with suppress(KeyError):
                self._incoming_stack.remove(command)
            with suppress(KeyError):
                self._scheduled_stack.remove(command)
            with suppress(KeyError):
                self._ended_stack.remove(command)

        if cancel_all:
            self._reset_all_stacks()

    def execute(self, fork: bool = False) -> Optional[Future]:
        """Perpetually run the event loop.

        :param fork: Fork a separate thread to run the event loop in. If
            `True`, a :py:class:`~concurrent.futures.Future` is
            returned. If `False` and an attempt is made to shut the
            event loop down via :py:meth:`~command_based_framework.scheduler.Scheduler.shutdown`
            in the same thread, a deadlock will occur.
        :type fork: bool

        :return: A :py:class:`~concurrent.futures.Future` if `fork` is
            `True`, otherwise `None`.
        :rtype: :py:class:`~concurrent.futures.Future`, None
        """  # noqa: DAR202

    def prestart_setup(self) -> None:
        """Run prestart checks and setup when :py:meth:`~command_based_framework.scheduler.Scheduler.execute` is called."""  # noqa: E501

    def register_subsystem(self, subsystem: "Subsystem") -> None:
        """Register a :py:class:`~command_based_framework.subsystems.Subsystem` with the scheduler.

        This should be called automatically by the subsystem upon
        creation, so calling this directly should not be necessary.
        Registered subsystems allow for default commands to be scheduled
        if the subsystem is not active in another command.

        :param subsystem: The subsystem to register.
        :type subsystem: :py:class:`~command_based_framework.subsystems.Subsystem`
        """  # noqa: E501
        self._subsystem_stack.add(subsystem)

    def run_once(self) -> None:
        """Run one complete loop of the scheduler's event loop."""
        self._poll_actions()
        self._schedule_default_commands()
        self._end_commands()
        self._init_commands()
        self._execute_commands()
        self._update_stack()

    def shutdown(self) -> None:
        """Shut the scheduler down.

        If :py:meth:`~command_based_framework.scheduler.Scheduler.execute`
        was called, calling this from the same thread will deadlock.
        """

    def _end_commands(self) -> None:
        for cmd in self._ended_stack:
            with cmd:
                cmd.end(interrupted=False)
            self._scheduled_stack.remove(cmd)

            # Reset all requirements' current commands to none
            for requirement in cmd.requirements:
                requirement.current_command = None

            # Reset the interrupt flag
            cmd.needs_interrupt  # noqa: WPS428

    def _execute_commands(self) -> None:
        for command in self._scheduled_stack.copy():
            # Check if the command is finished before executing it
            # Safer to do this check first
            if command.is_finished():
                with command:
                    command.end(interrupted=False)
                self._scheduled_stack.remove(command)

                # Reset all requirement's current commands to none
                for requirement in command.requirements:
                    requirement.current_command = None

                # Reset the interrupt flag
                command.needs_interrupt  # noqa: WPS428
                self._ended_stack.add(command)
                continue

            # Execute the command
            with command:
                command.execute()

            # Immediately interrupt the command if needed
            if command.needs_interrupt:
                self.cancel(command)

    def _execute_subsystems(self) -> None:
        for subsystem in self._subsystem_stack:
            with subsystem:
                subsystem.periodic()

    def _init_commands(self) -> None:  # noqa: C901, WPS231
        for command in self._incoming_stack.copy():
            # If the command is already scheduled, don't init
            if command in self._scheduled_stack:
                self._incoming_stack.remove(command)
                continue

            # If the command shares requirements with other commands in
            # the stack, don't init
            skip = False
            for cmd in self._incoming_stack.copy():
                if cmd == command:
                    continue

                if cmd.requirements.intersection(command.requirements):
                    self._incoming_stack.remove(command)
                    skip = True
            if skip:
                continue

            # Interrupt other commands that use this command's
            # requirements
            for cmd in self._scheduled_stack.copy():
                if cmd.requirements.intersection(command.requirements):
                    # Verify the command is not in the interrupt or
                    # end stacks since they would have already finished
                    # by now
                    if cmd in self._ended_stack:
                        continue

                    # Cancel should automatically remove this cmd from
                    # all stacks
                    self.cancel(cmd)

            # Set all requirements current command to this incoming
            # command
            for requirement in command.requirements:
                requirement.current_command = command

            # Initialize this command
            with command:
                command.initialize()

            if command.needs_interrupt:
                # Cancel should automatically remove this cmd from
                # all stacks
                self.cancel(command)

    def _poll_actions(self) -> None:  # noqa: C901, WPS210, WPS231
        # Reimport Condition again since the top-level import will have
        # errored out and is only used for type-hints
        from command_based_framework.actions import Condition  # noqa: WPS442

        for action, conditions_commands in self._actions_stack.items():
            # Get the last and current state of the action
            # Update the last_state immediately since we are checking
            # the current state and the state may change
            last_state = action.last_state
            current_state = action.poll()
            action.last_state = current_state
            action_state = (last_state, current_state)

            # Handle each state type
            if action_state == (False, True):
                # When activated
                commands = conditions_commands.setdefault(
                    Condition.when_activated,
                    set(),
                )
                self._incoming_stack.update(commands)

                # Toggle when activated
                commands = conditions_commands.setdefault(
                    Condition.toggle_when_activated,
                    set(),
                )
                for command in commands:
                    if command in self._scheduled_stack:
                        self._ended_stack.add(command)
                    else:
                        self._incoming_stack.add(command)
            elif action_state == (True, True):
                # When held
                commands = conditions_commands.setdefault(Condition.when_held, set())
                self._incoming_stack.update(commands)
            elif action_state == (True, False):
                # When deactivated
                commands = conditions_commands.setdefault(
                    Condition.when_deactivated,
                    set(),
                )
                self._incoming_stack.update(commands)

                # When held
                # Need to be able to deactivate when held, which occurs
                # at the same time as when deactivated
                commands = conditions_commands.setdefault(Condition.when_held, set())
                self._ended_stack.update(commands)

    def _reset_all_stacks(self) -> None:
        self._all_stack = set()
        self._actions_stack = {}
        self._incoming_stack = set()
        self._scheduled_stack = set()
        self._ended_stack = set()
        self._subsystem_stack = set()

    def _schedule_default_commands(self) -> None:  # noqa: WPS231
        for subsystem in self._subsystem_stack:
            if subsystem.default_command and not subsystem.current_command:
                for command in self._incoming_stack.union(self._scheduled_stack):
                    if subsystem in command.requirements:
                        break
                else:
                    self._incoming_stack.add(subsystem.default_command)

    def _update_stack(self) -> None:
        # Remove interrupted and ended commands
        self._scheduled_stack.difference_update(self._ended_stack)

        # Move incoming commands to scheduled stack
        self._scheduled_stack.update(self._incoming_stack)
        self._all_stack.update(self._scheduled_stack)

        # Reset incoming, ended, and interrupted stacks
        self._incoming_stack.clear()
        self._ended_stack.clear()
