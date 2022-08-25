from contextlib import suppress
from typing import Optional

from command_based_framework._common import ContextManagerMixin
from command_based_framework.scheduler import Scheduler

with suppress(ImportError):
    from command_based_framework.commands import Command


class Subsystem(ContextManagerMixin):
    """Breaks out complex robot components into methods and attributes.

    Subsystems define how something is performed; i.e. reading a sensor.
    Subsystems are also used by the scheduler to ensure two commands are
    not using the same resources simultaneously.
    """

    # The name of the subsystem
    _name: str

    # The command that is currently using this subsystem
    _current_command: Optional["Command"]

    # The command that will run whenever this subsystem is not being
    # used
    _default_command: Optional["Command"]

    def __init__(self, name: Optional[str] = None) -> None:
        """Creates a new `Subsystem` instance.

        When created, the subsystem will automatically register itself
        with the scheduler.

        :param name: The name of the subsystem. If not provided, the
            class name is used instead.
        :type name: str, optional
        """
        super().__init__()
        self._name = name or self.__class__.__name__
        self._current_command = None
        self._default_command = None

        # Register this subsystem in the scheduler's stack
        Scheduler.instance.register_subsystem(self)  # type: ignore

    @property
    def current_command(self) -> Optional["Command"]:
        """The command that is currently using this subsystem.

        This property is controlled by the scheduler and should not be
        modified directly.

        If no default command is set and no command is currently using
        this subsystem, then this property will be `None`.
        """
        return self._current_command

    @current_command.setter
    def current_command(self, command: Optional["Command"]) -> None:
        self._current_command = command

    @property
    def default_command(self) -> Optional["Command"]:
        """The command to run when no other command is active.

        If not specified, then this subsystem will remain idle.

        Default commands **must** require the subsystems they are
        assigned to. A :py:exc:`ValueError` will be raised otherwise.
        """
        return self._default_command

    @default_command.setter
    def default_command(self, command: Optional["Command"]) -> None:
        # Ensure the command requires this subsystem
        if command and self not in command.requirements:
            raise ValueError(
                (
                    "{name} must have {name2} as a requirement "
                    "before being assigned as a default"
                ).format(
                    name=command.name,
                    name2=self.name,
                ),
            )
        self._default_command = command

    @property
    def name(self) -> str:
        """The name of the subsystem.

        This is a read-only property.

        If one was not provided at the creation of the command, the
        class name is used instead.
        """
        return self._name

    def periodic(self) -> None:
        """Periodically called when the subsystem is required by a scheduled :py:class:`~command_based_framework.commands.Command`.

        Override this behavior to always execute by calling
        :py:meth:`~command_based_framework.scheduler.Scheduler.register_subsystem`.
        """  # noqa: E501
