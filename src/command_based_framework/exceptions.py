class CommandBasedFrameworkException(Exception):
    """Base exception for all framework exceptions."""


class SchedulerExistsError(CommandBasedFrameworkException):
    """A scheduler instance already exists.

    Only one scheduler may exist at any given time. More than one would
    allow undefined behavior to occur in terms of resource allocation
    and usage.

    Instead, use :py:class:`~command_based_framework.scheduler.Scheduler`'s
    :py:obj:`~command_based_framework.scheduler.SchedulerMeta.instance`
    or delete all references to the current scheduler and recreate it.
    """  # noqa: E501
