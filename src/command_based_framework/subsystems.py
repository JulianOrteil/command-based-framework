from command_based_framework._common import ContextManagerMixin


class Subsystem(ContextManagerMixin):
    """Breaks out complex robot components into methods and attributes.

    Subsystems define how something is performed; i.e. reading a sensor.
    Subsystems are also used by the scheduler to ensure two commands are
    not using the same resources simultaneously.
    """

    def periodic(self) -> None:
        """Periodically called when the subsystem is required by a scheduled :py:class:`~command_based_framework.commands.Command`.

        Override this behavior to always execute by calling
        :py:meth:`~command_based_framework.scheduler.Scheduler.register_subsystem`.
        """  # noqa: E501
