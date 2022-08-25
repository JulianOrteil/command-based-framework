from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler
from command_based_framework.subsystems import Subsystem


def test_current_and_default_commands() -> None:
    """Verify current and default commands get set"""
    scheduler = Scheduler.instance or Scheduler()

    class MyCommand(Command):
        def execute(self) -> None:
            return super().execute()

        def is_finished(self) -> bool:
            return super().is_finished()

    class MySubsystem(Subsystem):
        def periodic(self) -> None:
            return super().periodic()

    command = MyCommand()
    subsystem = MySubsystem()

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
