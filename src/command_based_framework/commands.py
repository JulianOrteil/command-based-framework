import itertools
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from threading import Barrier, Event
from types import TracebackType
from typing import Iterator, Optional, Set, Tuple, Type

from command_based_framework._common import CommandType, ContextManagerMixin
from command_based_framework.scheduler import Scheduler
from command_based_framework.subsystems import Subsystem


class CommandState(Enum):
    """The state of a command in the scheduler."""

    # Command is not scheduled (cancelled, ended, not yet ran)
    idle = auto()

    # Command has initialized
    initialized = auto()

    # Command is executing
    executing = auto()


class Command(ContextManagerMixin):  # noqa: WPS214
    """Executes a process when activated by an :class:`~command_based_framework.actions.Action`.

    Commands dictate what subsystems do at what time. They are scheduled
    when a :meth:`~command_based_framework.actions.Action.poll`
    bound condition is met. Commands are also synchronous, meaning they
    are always blocking the scheduler's event loop and should complete
    quickly.

    Commands have the following life cycle in the scheduler:

    - New commands have their :meth:`~Command.initialize` method called.
    - Actions bound to this command have their
        :meth:`~command_based_framework.actions.Action.poll` method called.
        Depending on how a command is bound to an action, the scheduler may
        skip directly to step 4 for a command.
    - The scheduler now periodically executes these new commands by
        calling their :meth:`~Command.is_finished` and
        :meth:`~Command.execute` methods, in that order.
    - Whether through an interrupt or :meth:`~Command.is_finished`,
        commands have their :meth:`~Command.end` methods called and are
        removed from the scheduled command stack.

    Commands also maintain their state after being unscheduled as long
    as a reference is maintained. The scheduler maintains a reference as
    long as the command is scheduled, but releases it immediately after.
    """  # noqa: E501

    # The name of the command
    _name: str

    # Requirements are the subsystems required for this command to run.
    # The scheduler uses this to ensure only one command is using a
    # subsystem at any time
    _requirements: Set[Subsystem]

    # Indicates whether or not the command needs to be interrupted after
    # encountering an error
    _needs_interrupt: bool

    # Tracks the current state of the command so the scheduler can more
    # easily determine how to schedule it
    _state: CommandState

    def __init__(self, name: Optional[str] = None, *subsystems: Subsystem) -> None:
        """Creates a new :class:`Command` instance.

        Args:
            name: The name of the command. If not provided, the default,
                then the name of the class is used.
            subsystems: Variable length of subsystems the command uses.
        """  # noqa: RST203
        super().__init__()
        self._name = name or self.__class__.__name__
        self._requirements = set()
        self._needs_interrupt = False
        self._state = CommandState.idle

        # Register each subsystem as a requirements
        self.add_requirements(*subsystems)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> bool:
        """Called when the command exits a context manager."""
        # Ignore non-errors
        if not exc_type or not exc or not traceback:
            return True

        handled = self.handle_exception(exc_type, exc, traceback)
        self.needs_interrupt = not handled or not isinstance(handled, bool)
        return True

    def __repr__(self) -> str:
        """Unicode representation of the class."""
        return self.__str__()

    def __str__(self) -> str:
        """Unicode representation of the class."""
        return "<{name}>".format(name=self.name)

    @property
    def name(self) -> str:
        """The name of the command.

        This is a read-only property.

        If one was not provided at the creation of the command, the
        class name is used instead.
        """
        return self._name

    @property
    def needs_interrupt(self) -> bool:
        """Indicates if the command needs to be interrupted.

        This property should not be set directly as it is managed by the
        scheduler.

        Every read of this property resets its state.
        """
        ret = self._needs_interrupt
        self.needs_interrupt = False
        return ret

    @needs_interrupt.setter
    def needs_interrupt(self, state: bool) -> None:
        self._needs_interrupt = state

    @property
    def requirements(self) -> Set[Subsystem]:
        """The subsystems this command requires to run.

        This is a read-only property.
        """
        return self._requirements

    @property
    def state(self) -> CommandState:
        """The state of the command.

        Automatically set by the scheduler.
        """
        return self._state

    @state.setter
    def state(self, state: CommandState) -> None:
        self._state = state

    def add_requirements(self, *subsystems: Subsystem) -> None:
        """Register any number of subsystems as a command requirement.

        Only one command can be running with any given requirement. If
        two commands share any requirement and are scheduled to run,
        which command runs may be undefined. If one command is already
        scheduled then it will be interrupted by the newly scheduled
        command.
        """
        self._requirements.update(set(subsystems))

    def initialize(self) -> None:
        """Called each time the command in scheduled.

        Any initialization or pre-execution code should go here.
        """
        raise NotImplementedError

    def execute(self) -> None:
        """Periodically called while the command is scheduled.

        All execution code should go here.
        """
        raise NotImplementedError

    def end(self, interrupted: bool) -> None:
        """Called once the command has been unscheduled.

        Any clean up or post-execution code should go here.

        Args:
            interrupted: Flag indicating if the command was interrupted
                and needs to end. Also means
                :meth:`~Command.is_finished` was not checked.
        """  # noqa: DAR401
        raise NotImplementedError

    def is_finished(self) -> bool:
        """Periodically called before :meth:`~Command.execute` while the command is scheduled.

        Returns:
            `True` if the command should end.
        """  # noqa: E501, DAR202, DAR401
        raise NotImplementedError


class WaitCommand(Command):
    """A command that waits for a specified period of time."""

    _delay: float
    _start: float

    def __init__(self, name: Optional[str] = None, delay: float = 0) -> None:
        """Creates a new :class:`~WaitCommand` instance.

        Args:
            name: The name of the command. If not provided, the class
                name is used instead.
            delay: How long to wait for in seconds. Defaults to `0` (no
                wait).
        """
        super().__init__(name)
        self._delay = delay

    def initialize(self) -> None:
        """Record the start time."""
        self._start = time.time()

    def execute(self) -> None:
        """Not implemented."""

    def is_finished(self) -> bool:
        """Check whether the specified amount of time has passed."""
        return time.time() - self._start >= self._delay

    def end(self, interrupted: bool) -> None:
        """Not implemented."""


class CommandGroup(Command):
    """Group commands into a single manageable interface.

    Only provides a modified command `__init__` method which accepts
    commands instead of subsystems. Also requires all subsystems by any
    passed commands which may share requirements. Note this behavior may
    change on child classes of this abstract.

    Any command or group can be provided to this abstract.
    """

    _commands: Tuple[CommandType, ...]

    def __init__(self, name: Optional[str] = None, *commands: CommandType) -> None:
        """Creates a new :class:`~CommandGroup` instance.

        Args:
            name: The name of the command group. If not provided, the
                class name is used instead.
            commands: Variable length of commands to group.
        """  # noqa: RST203
        super().__init__(name)

        # Require all subsystems
        for command in commands:
            self.add_requirements(*command.requirements)

        self._commands = commands


class SequentialCommandGroup(CommandGroup):
    """Sequentially executes commands.

    The order which commands are provided to the constructor determines
    the order the commands are executed. If any commands error or are
    interrupted, no further commands will be executed.

    Any command or group can be provided to the constructor.
    """

    _sequence: Iterator[CommandType]
    _current_command: Optional[CommandType]
    _end_of_sequence: bool

    def __init__(self, name: Optional[str] = None, *commands: CommandType) -> None:
        """Creates a new :class:`~SequentialCommandGroup` instance.

        Args:
            name: The name of the command group. If not provided, the
                class name is used instead.
            commands: Variable length of commands to group.
        """  # noqa: RST203
        super().__init__(name, *commands)
        self._end_of_sequence = False
        self._current_command = None

    def initialize(self) -> None:
        """Select the first command in the chain to run."""
        self._end_of_sequence = False
        self._current_command = None
        self._sequence = iter(self._commands)
        self._prepare_next_command()

    def execute(self) -> None:
        """Execute the currently sequenced command."""
        # mypy fix, check if self._current_command is set
        if not self._current_command:  # pragma: no cover
            self._end_of_sequence = True
            return

        # Check if the current command has finished
        # If so, end it and prepare the next one
        if self._current_command.is_finished():
            self._current_command.end(interrupted=False)
            self._prepare_next_command()
            return

        # Execute the current command
        self._current_command.execute()

    def is_finished(self) -> bool:
        """Check if the end of the chain has been reached."""
        return self._end_of_sequence or not self._current_command

    def end(self, interrupted: bool) -> None:
        """End the current command."""
        if self._current_command:
            self._current_command.end(interrupted=interrupted)

    def _prepare_next_command(self) -> None:
        if self._current_command is None:
            self._current_command = self._commands[0]
        else:
            try:
                self._current_command = next(self._sequence)
            except StopIteration:
                self._current_command = None
                self._end_of_sequence = True
                return

        # Initialize the command
        self._current_command.initialize()


class ParallelCommandGroup(CommandGroup):
    """Run multiple commands in parallel.

    Each command will execute in its own dedicated thread. Unlike most
    other command groups, commands submitted here cannot share
    requirements.
    """

    _pool: ThreadPoolExecutor
    _finished: Barrier
    _sentinel: Event

    def __init__(  # noqa: WPS231
        self,
        name: Optional[str] = None,
        *commands: CommandType,
    ) -> None:
        """Creates a new :class:`ParallelCommandGroup` instance.

        Args:
            name: The name of the command group. If not provided, the
                class name is used instead.
            commands: Variable length of commands to group.

        Raises:
            ValueError: Overlapping requirements were detected amongst
                the commands provided.
        """  # noqa: RST203
        # Don't pass the commands to the parent class, we have to
        # implement custom checking of them here
        super().__init__(name)

        # Check for shared requirements
        for command in commands:
            for cmd in commands:
                if cmd == command:
                    continue
                if cmd.requirements.intersection(command.requirements):
                    raise ValueError(
                        "{cmd1} has shared requirements with {cmd2}".format(
                            cmd1=command,
                            cmd2=cmd,
                        ),
                    )
            self.add_requirements(*command.requirements)

        self._commands = commands
        self._sentinel = Event()

    def initialize(self) -> None:
        """Submit all commands to the thread pool."""
        self._sentinel.clear()
        self._pool = ThreadPoolExecutor(len(self._commands) + 1)
        self._finished = Barrier(len(self._commands) + 1)
        self._pool.map(
            self._execute,
            self._commands,
            itertools.repeat(self._finished),
            itertools.repeat(self._sentinel),
        )

    def execute(self) -> None:
        """Not implemented."""

    def is_finished(self) -> bool:
        """Check if all commands have finished."""
        # Do not catch BrokenPipeErrors
        # We want to ensure commands are interrupted in the event
        # something unexpected occurs
        return self._finished.n_waiting == len(self._commands)

    def end(self, interrupted: bool) -> None:
        """Wait for all commands to finish executing."""
        self._sentinel.set()
        self._finished.wait()
        self._pool.shutdown(wait=True)

    def _execute(
        self,
        command: CommandType,
        finished: Barrier,
        sentinel: Event,
    ) -> None:
        try:  # noqa: WPS229
            # Initialize the command
            command.initialize()

            # Run an event loop
            while True:
                # Check if the current command has finished
                if command.is_finished():
                    command.end(interrupted=False)
                    return

                # Check if the thread pool is shutting down
                if sentinel.is_set():
                    command.end(interrupted=True)
                    return

                # Execute the current command
                command.execute()

                time.sleep(Scheduler.get_instance().clock_speed)  # type: ignore
        except Exception:
            # Handle errors
            command.handle_exception(*sys.exc_info())
            command.end(interrupted=True)

            # Stop execution
            sentinel.set()
        finally:
            finished.wait()
