from abc import ABC, abstractmethod

from command_based_framework.scheduler import Scheduler


class CommandBasedRobot(ABC, Scheduler):
    """A template to ease the creation of a compatible system.

    This template breaks out all major aspects of the framework into
    clearly defined methods of ease-of-use. There is a specific order
    in which these methods are executed.
    """

    @abstractmethod
    def bind_components(self) -> None:
        """Bind all action `whens` to commands in this method."""

    @abstractmethod
    def create_actions(self) -> None:
        """Define and instantiate actions in this method."""

    @abstractmethod
    def create_commands(self) -> None:
        """Define and instantiate commands in this method."""

    @abstractmethod
    def create_inputs(self) -> None:
        """Define and instantiate any inputs in this method."""

    @abstractmethod
    def create_subsystems(self) -> None:
        """Define and instantiate subsystems in this method."""

    def prestart_setup(self) -> None:
        """Called just before the event loop starts.

        Handles the calling of all `create` methods within this class.
        The order in which these are called is as follows:

        **1.** :py:meth:`~command_based_framework.robot.CommandBasedRobot.create_inputs`

        **2.** :py:meth:`~command_based_framework.robot.CommandBasedRobot.create_subsystems`

        **3.** :py:meth:`~command_based_framework.robot.CommandBasedRobot.create_commands`

        **4.** :py:meth:`~command_based_framework.robot.CommandBasedRobot.create_actions`

        **5.** :py:meth:`~command_based_framework.robot.CommandBasedRobot.bind_components`
        """  # noqa: E501
        self.create_inputs()
        self.create_subsystems()
        self.create_commands()
        self.create_actions()
        self.bind_components()

    def postend_teardown(self) -> None:
        """Called just after the event loop ends.

        Any post-execution code should go here.
        """
