import sys
from contextlib import suppress
from types import TracebackType
from typing import Callable, Optional, Type, Union

if sys.version_info >= (3, 10):
    # WPS433: Found nested import
    # WPS440: Found block variables overlap
    from typing import TypeAlias  # noqa: WPS433, WPS440; pragma: no cover
else:
    # WPS433: Found nested import
    # WPS440: Found block variables overlap
    from typing_extensions import TypeAlias  # noqa: WPS433, WPS440; pragma: no cover

with suppress(ImportError):
    from command_based_framework.commands import Command, CommandGroup

CommandType: TypeAlias = Union["Command", "CommandGroup"]
CallableCommandType: TypeAlias = Union[CommandType, Callable[[], CommandType]]


class ContextManagerMixin(object):
    """Mixin providing context manager support.

    Also contains a :meth:`~ContextManagerMixin.handle_exception`
    which is called by the scheduler whenever the parent child instance
    raises an error. Use this method to process the exception.
    """  # noqa: E501

    def __enter__(self) -> "ContextManagerMixin":
        """Called when the command enters a context manager."""
        return self

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

        self.handle_exception(exc_type, exc, traceback)
        return True

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc: BaseException,
        traceback: TracebackType,
    ) -> bool:
        """Called when any method raises an error.

        If a command, the scheduler uses the output of this method to
        determine whether the command should be immediately interrupted.

        Args:
            exc_type: The type of exception raised.
            exc: The exception itself.
            traceback: The stack trace for logging purposes.

        Returns:
            `True` to indicate the error has been handled or `False`
            otherwise. If `False`, the command raising the error will be
            interrupted.
        """
        return False  # pragma: no cover
