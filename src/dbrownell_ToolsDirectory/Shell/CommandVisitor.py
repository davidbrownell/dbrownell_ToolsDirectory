# noqa: D100
from abc import abstractmethod, ABC

from dbrownell_ToolsDirectory.Shell.Commands import (
    Command,
    Message,
    Call,
    Execute,
    Set,
    Augment,
    Exit,
    ExitOnError,
    EchoOff,
    PersistError,
    PushDirectory,
    PopDirectory,
    Raw,
)


# ----------------------------------------------------------------------
class CommandVisitor(ABC):
    """Abstract base class for a visitor that processes shell commands."""

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        self._dispatcher = {
            Message: self.OnMessage,
            Call: self.OnCall,
            Execute: self.OnExecute,
            Set: self.OnSet,
            Augment: self.OnAugment,
            Exit: self.OnExit,
            ExitOnError: self.OnExitOnError,
            EchoOff: self.OnEchoOff,
            PersistError: self.OnPersistError,
            PushDirectory: self.OnPushDirectory,
            PopDirectory: self.OnPopDirectory,
            Raw: self.OnRaw,
        }

    # ----------------------------------------------------------------------
    def Accept(self, command: Command) -> str | None:
        """Accept a command and dispatch it to the appropriate handler."""

        handler = self._dispatcher.get(type(command))
        if handler is None:
            msg = f"No handler for command type: '{command.__class__.__name__}'"
            raise TypeError(msg)

        return handler(command)  # ty: ignore[invalid-argument-type]

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @abstractmethod
    def OnMessage(
        self,
        command: Message,
    ) -> str | None:
        """Process a Message command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnCall(
        self,
        command: Call,
    ) -> str | None:
        """Process a Call command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnExecute(
        self,
        command: Execute,
    ) -> str | None:
        """Process an Execute command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnSet(
        self,
        command: Set,
    ) -> str | None:
        """Process a Set command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnAugment(
        self,
        command: Augment,
    ) -> str | None:
        """Process an Augment command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnExit(
        self,
        command: Exit,
    ) -> str | None:
        """Process an Exit command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnExitOnError(
        self,
        command: ExitOnError,
    ) -> str | None:
        """Process an ExitOnError command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnEchoOff(
        self,
        command: EchoOff,
    ) -> str | None:
        """Process an EchoOff command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnPersistError(
        self,
        command: PersistError,
    ) -> str | None:
        """Process a PersistError command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnPushDirectory(
        self,
        command: PushDirectory,
    ) -> str | None:
        """Process a PushDirectory command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnPopDirectory(
        self,
        command: PopDirectory,
    ) -> str | None:
        """Process a PopDirectory command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    def OnRaw(
        self,
        command: Raw,
    ) -> str | None:
        """Process a Raw command."""
        raise Exception("Abstract method")  # noqa: EM101, TRY003  # pragma: no cover
