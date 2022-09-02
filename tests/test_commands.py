from command_based_framework.commands import Command


def test_name() -> None:
    """Verify the name of commands are set properly."""
    class MyCommand(Command):
        def is_finished(self) -> bool:
            return False
        def execute(self) -> None:
            return None

    command1 = MyCommand()
    command2 = MyCommand(name="HelloWorld")

    assert command1.name == "MyCommand"
    assert command2.name == "HelloWorld"
    assert str(command1) == "<MyCommand>"


def test_needs_interrupt() -> None:
    """Verify the needs interrupt property sets properly."""

    class MyCommand(Command):

        def handle_exception(self,*_) -> bool:
            return False

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            raise ValueError("test error")

    command = MyCommand()

    # Simulate executing a command
    with command:
        command.execute()

    # Verify the property is set
    assert command.needs_interrupt

    # Verify reading the property reset it
    assert not command.needs_interrupt
