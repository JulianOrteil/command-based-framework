class CommandBasedFrameworkError(Exception):
    """Base exception for all framework exceptions."""


class SchedulerExistsError(CommandBasedFrameworkError):
    """A scheduler instance already exists.

    Only one scheduler may exist at any given time. More than one would
    allow undefined behavior to occur in terms of resource allocation
    and usage.

    Instead, use :class:`~command_based_framework.scheduler.Scheduler`'s
    :meth:`~command_based_framework.scheduler.Scheduler.get_instance()`
    or delete all references to the current scheduler and recreate it.
    """
