from abc import ABC, abstractmethod
from typing import Optional

from command_based_framework.subsystems import Subsystem


class Command(ABC):
    """Executes a process when activated by an :py:class:`~command_based_framework.actions.Action`.

    Commands dictate what subsystems do at what time. They are scheduled
    when a :py:class:`~command_based_framework.actions.Action.poll`
    bound condition is met. Commands are also synchronous, meaning they
    are always blocking the scheduler's event loop and should complete
    quickly.

    Commands have the following life cycle in the scheduler:
    1. New commands have their `initialize` method called.
    2. Actions bound to this command have their `poll` method called.
    Depending on how a command is bound to an action, the command may
    skip directly to step 4.
    3. The scheduler now periodically executes these new commands by
    calling their `is_finished` and `execute` methods, in that order.
    4. Whether through an action or `is_finished`, commands have their
    `end` methods called and are removed from the stack.

    Commands also maintain their state after being unscheduled as long
    as a reference is maintained. The scheduler maintains a reference as
    long as the command is scheduled, but releases it immediately after.
    """  # noqa: E501

    def __init__(self, name: Optional[str] = None) -> None:
        """Creates a new `Command` instance."""
        super().__init__()

    def add_requirements(self, *subsystems: Subsystem) -> None:
        """Register any number of subsystems as a command requirement.

        Only one command can be running with any given requirement. If
        two commands share any requirement and are scheduled to run,
        which command runs may be undefined. If one command is already
        scheduled then it will be interrupted by the newly scheduled
        command.
        """

    def initialize(self) -> None:
        """Called each time the command in scheduled.

        Any intialization or pre-execution code should go here.
        """

    def execute(self) -> None:
        """Periodically called while the command is scheduled.

        All execution code should go here.
        """

    def end(self, interrupted: bool) -> None:
        """Called once the command has been unscheduled.

        Any clean up or post-execution code should go here.
        `interrupted` will be `True` if the command was interrupted for
        any reason.
        """

    @abstractmethod
    def is_finished(self) -> bool:
        """Periodically called before :py:meth:`~command_based_framework.commands.Command.execute` while the command is scheduled.

        Return `True` when the command should end.
        """  # noqa: E501
