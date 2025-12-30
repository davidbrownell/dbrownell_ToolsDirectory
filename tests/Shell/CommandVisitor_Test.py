from unittest.mock import Mock

import pytest

from dbrownell_Common.Types import override

from dbrownell_ToolsDirectory.Shell.Commands import *
from dbrownell_ToolsDirectory.Shell.CommandVisitor import CommandVisitor


# ----------------------------------------------------------------------
class MyCommandVisitor(CommandVisitor):
    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self.mock = Mock()

    # ----------------------------------------------------------------------
    @property
    def result(self) -> str:
        assert self.mock.call_count == 1
        return self.mock.mock_calls[0].args[0]  #

    # ----------------------------------------------------------------------
    @override
    def OnMessage(
        self,
        command: Message,
    ) -> str | None:
        self.mock("OnMessage")

    # ----------------------------------------------------------------------
    @override
    def OnCall(
        self,
        command: Call,
    ) -> str | None:
        self.mock("OnCall")

    # ----------------------------------------------------------------------
    @override
    def OnExecute(
        self,
        command: Execute,
    ) -> str | None:
        self.mock("OnExecute")

    # ----------------------------------------------------------------------
    @override
    def OnSet(
        self,
        command: Set,
    ) -> str | None:
        self.mock("OnSet")

    # ----------------------------------------------------------------------
    @override
    def OnAugment(
        self,
        command: Augment,
    ) -> str | None:
        self.mock("OnAugment")

    # ----------------------------------------------------------------------
    @override
    def OnExit(
        self,
        command: Exit,
    ) -> str | None:
        self.mock("OnExit")

    # ----------------------------------------------------------------------
    @override
    def OnExitOnError(
        self,
        command: ExitOnError,
    ) -> str | None:
        self.mock("OnExitOnError")

    # ----------------------------------------------------------------------
    @override
    def OnEchoOff(
        self,
        command: EchoOff,
    ) -> str | None:
        self.mock("OnEchoOff")

    # ----------------------------------------------------------------------
    @override
    def OnPersistError(
        self,
        command: PersistError,
    ) -> str | None:
        self.mock("OnPersistError")

    # ----------------------------------------------------------------------
    @override
    def OnPushDirectory(
        self,
        command: PushDirectory,
    ) -> str | None:
        self.mock("OnPushDirectory")

    # ----------------------------------------------------------------------
    @override
    def OnPopDirectory(
        self,
        command: PopDirectory,
    ) -> str | None:
        self.mock("OnPopDirectory")

    # ----------------------------------------------------------------------
    @override
    def OnRaw(
        self,
        command: Raw,
    ) -> str | None:
        self.mock("OnRaw")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def test_Message() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Message(Mock()))
    assert visitor.result == "OnMessage"


# ----------------------------------------------------------------------
def test_OnCall() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Call(Mock()))
    assert visitor.result == "OnCall"


# ----------------------------------------------------------------------
def test_Execute() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Execute(Mock()))
    assert visitor.result == "OnExecute"


# ----------------------------------------------------------------------
def test_Set() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Set(Mock(), Mock()))
    assert visitor.result == "OnSet"


# ----------------------------------------------------------------------
def test_Augment() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Augment(Mock(), Mock()))
    assert visitor.result == "OnAugment"


# ----------------------------------------------------------------------
def test_Exit() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Exit())
    assert visitor.result == "OnExit"


# ----------------------------------------------------------------------
def test_ExitOnError() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(ExitOnError())
    assert visitor.result == "OnExitOnError"


# ----------------------------------------------------------------------
def test_EchoOff() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(EchoOff())
    assert visitor.result == "OnEchoOff"


# ----------------------------------------------------------------------
def test_PersistError() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(PersistError(Mock()))
    assert visitor.result == "OnPersistError"


# ----------------------------------------------------------------------
def test_PushDirectory() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(PushDirectory(Mock()))
    assert visitor.result == "OnPushDirectory"


# ----------------------------------------------------------------------
def test_PopDirectory() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(PopDirectory())
    assert visitor.result == "OnPopDirectory"


# ----------------------------------------------------------------------
def test_Raw() -> None:
    visitor = MyCommandVisitor()

    visitor.Accept(Raw(Mock()))
    assert visitor.result == "OnRaw"


# ----------------------------------------------------------------------
def test_InvalidCommand() -> None:
    # ----------------------------------------------------------------------
    class InvalidCommand(Command):
        pass

    # ----------------------------------------------------------------------

    with pytest.raises(TypeError, match="No handler for command type: 'InvalidCommand'"):
        MyCommandVisitor().Accept(InvalidCommand())
