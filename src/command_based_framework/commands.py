from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type

from command_based_framework.subsystems import Subsystem


class Command(ABC):
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

    def __init__(self, name: Optional[str] = None) -> None:
        """Creates a new `Command` instance.

        :param name: The name of the command. If not provided, the class
            name is used instead.
        :type name: str, optional
        """
        super().__init__()

    def add_requirements(self, *subsystems: Subsystem) -> None:
        """Register any number of subsystems as a command requirement.

        Only one command can be running with any given requirement. If
        two commands share any requirement and are scheduled to run,
        which command runs may be undefined. If one command is already
        scheduled then it will be interrupted by the newly scheduled
        command.
        """

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc: BaseException,
        traceback: TracebackType,
    ) -> Optional[bool]:
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
