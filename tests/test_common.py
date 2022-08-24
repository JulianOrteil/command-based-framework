from command_based_framework._common import ContextManagerMixin


def test_ctx_man_mixin() -> None:
    """Verify the ctx manager mixin works correctly."""

    class MyClass(ContextManagerMixin):
        called_handled_exception = False

        def handle_exception(self, *exc):
            self.called_handled_exception = True

        def raise_error(self) -> None:
            raise ValueError("test error")

    with MyClass() as myclass:
        myclass.raise_error()
        assert myclass.called_handled_exception

    with MyClass() as myclass:
        # Do nothing, just exit
        pass
