from command_based_framework.scheduler import Scheduler


class CommandBasedRobot(Scheduler):
    """The main robot implementation to create and connect components."""

    def bind_components(self) -> None:
        """Bind all action `whens` to commands in this method."""

    def create_actions(self) -> None:
        """Define and instantiate actions in this method."""

    def create_commands(self) -> None:
        """Define and instantiate commands in this method."""

    def create_inputs(self) -> None:
        """Define and instantiate any inputs in this method."""

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
