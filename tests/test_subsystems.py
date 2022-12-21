import pytest

from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler
from command_based_framework.subsystems import Subsystem

def test_name() -> None:
    """Verify the name of subsystems are set properly."""
    scheduler = Scheduler.get_instance() or Scheduler()

    class MySubsystem(Subsystem):
        def is_finished(self) -> bool:
            return False
        def execute(self) -> None:
            return None

    subsystem1 = MySubsystem()
    subsystem2 = MySubsystem(name="HelloWorld")

    assert subsystem1.name == "MySubsystem"
    assert subsystem2.name == "HelloWorld"


def test_current_and_default_commands() -> None:
    """Verify current and default commands get set"""
    scheduler = Scheduler.get_instance() or Scheduler()

    class MyCommand(Command):
        def execute(self) -> None:
            return super().execute()

        def is_finished(self) -> bool:
            return super().is_finished()

    class MySubsystem(Subsystem):
        def periodic(self) -> None:
            return super().periodic()

    subsystem = MySubsystem()
    command = MyCommand(None, subsystem)
    command_no_requirement = MyCommand()

    # Verify the commands are set
    subsystem.default_command = command
    assert subsystem.default_command == command
    assert subsystem.current_command == None

    subsystem.current_command = command
    assert subsystem.current_command == command

    subsystem.current_command = None
    subsystem.default_command = None
    assert subsystem.default_command == None
    assert subsystem.current_command == None

    # Verify the subsystem rejects default commands that don't require
    # it
    with pytest.raises(ValueError):
        subsystem.default_command = command_no_requirement
