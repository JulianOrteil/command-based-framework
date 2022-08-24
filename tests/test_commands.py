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
