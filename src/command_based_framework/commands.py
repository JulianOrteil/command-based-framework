from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Set, Type

from command_based_framework._common import ContextManagerMixin
from command_based_framework.subsystems import Subsystem


class Command(ABC, ContextManagerMixin):  # noqa: WPS214
    """Executes a process when activated by an :py:class:`~command_based_framework.actions.Action`.

    Commands dictate what subsystems do at what time. They are scheduled
    when a :py:meth:`~command_based_framework.actions.Action.poll`
    bound condition is met. Commands are also synchronous, meaning they
    are always blocking the scheduler's event loop and should complete
    quickly.

    Commands have the following life cycle in the scheduler:

    **1.** New commands have their :py:meth:`~command_based_framework.commands.Command.initialize`
    method called.

    **2.** Actions bound to this command have their :py:meth:`~command_based_framework.actions.Action.poll`
    method called. Depending on how a command is bound to an action, the
    scheduler may skip directly to step 4 for a command.

    **3.** The scheduler now periodically executes these new commands by
    calling their :py:meth:`~command_based_framework.commands.Command.is_finished`
    and :py:meth:`~command_based_framework.commands.Command.execute`
    methods, in that order.

    **4.** Whether through an action or :py:meth:`~command_based_framework.commands.Command.is_finished`,
    commands have their :py:meth:`~command_based_framework.commands.Command.end`
    methods called and are removed from the stack.

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

    def __init__(self, name: Optional[str] = None, *subsystems: Subsystem) -> None:
        """Creates a new `Command` instance.

        :param name: The name of the command. If not provided, the class
            name is used instead.
        :type name: str, optional
        :param subsystems: Variable length of subsystems to
            automatically require.
        :type subsystems: tuple
        """
        super().__init__()
        self._name = name or self.__class__.__name__
        self._requirements = set()
        self._needs_interrupt = False

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

    def add_requirements(self, *subsystems: Subsystem) -> None:
        """Register any number of subsystems as a command requirement.

        Only one command can be running with any given requirement. If
        two commands share any requirement and are scheduled to run,
        which command runs may be undefined. If one command is already
        scheduled then it will be interrupted by the newly scheduled
        command.
        """
        self._requirements.update(set(subsystems))

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc: BaseException,
        traceback: TracebackType,
    ) -> bool:
        """Called when :py:meth:`~command_based_framework.commands.Command.execute` raises an error.

        The scheduler uses the output of this method to determine
        whether the command should be immediately interrupted.

        :param exc_type: The type of exception raised.
        :type exc_type: :py:class:`Type`
        :param exc: The exception raised.
        :type exc: :py:class:`Exception`
        :param traceback: The frame traceback of the error.
        :type traceback: :py:class:`Traceback`

        :return: `True` to indicate the error is handled. All other
            returns to the scheduler will be interpreted as the command
            needing to be immediately interrupted.
        :rtype: bool
        """  # noqa: DAR202

    def initialize(self) -> None:
        """Called each time the command in scheduled.

        Any initialization or pre-execution code should go here.
        """

    @abstractmethod
    def execute(self) -> None:
        """Periodically called while the command is scheduled.

        All execution code should go here.
        """

    def end(self, interrupted: bool) -> None:
        """Called once the command has been unscheduled.

        Any clean up or post-execution code should go here.

        :param interrupted: the command was interrupted, not ended.
        :type interrupted: bool
        """

    @abstractmethod
    def is_finished(self) -> bool:
        """Periodically called before :py:meth:`~command_based_framework.commands.Command.execute` while the command is scheduled.

        :return: `True` if the command should end, otherwise `False`.
        :rtype: bool
        """  # noqa: E501
