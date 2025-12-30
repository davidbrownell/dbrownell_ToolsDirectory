# noqa: D100
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Command:
    """Base class for all commands."""


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Message(Command):
    """Message displayed to the user."""

    value: str


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Call(Command):
    """Call another command; changes made by the called script are persisted."""

    command_line: str
    exit_on_error: bool = field(default=True, kw_only=True)
    exit_via_return_statement: bool = field(default=False, kw_only=True)


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Execute(Command):
    """Call another executable; changes made by the called executable are not persisted."""

    command_line: str
    exit_on_error: bool = field(default=True, kw_only=True)
    exit_via_return_statement: bool = field(default=False, kw_only=True)

    # ----------------------------------------------------------------------
    def __post_init__(self) -> None:
        assert not self.exit_via_return_statement or self.exit_on_error


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Set(Command):
    """Set an environment variable, overwriting any existing value."""

    name: str
    value_or_values: str | list[str] | None

    # ----------------------------------------------------------------------
    def EnumValues(self) -> Generator[str]:
        """Enumerate the values provided."""

        if isinstance(self.value_or_values, str):
            yield self.value_or_values
            return

        if isinstance(self.value_or_values, list):
            yield from self.value_or_values
            return

        if self.value_or_values is None:
            return

        assert False, type(self.value_or_values)  # noqa: B011, PT015 # pragma: no cover


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Augment(Command):
    """Augment an environment variable."""

    name: str
    value_or_values: str | list[str]
    append_values: bool = field(default=False, kw_only=True)

    # ----------------------------------------------------------------------
    def EnumValues(self) -> Generator[str]:
        """Enumerate the values provided."""

        if isinstance(self.value_or_values, str):
            yield self.value_or_values
            return

        if isinstance(self.value_or_values, list):
            yield from self.value_or_values
            return

        assert False, type(self.value_or_values)  # noqa: B011, PT015 # pragma: no cover


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Exit(Command):
    """Exit the script with an optional return code."""

    pause_on_success: bool = field(default=False, kw_only=True)
    pause_on_error: bool = field(default=False, kw_only=True)
    return_code: int | None = field(default=None, kw_only=True)


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ExitOnError(Command):
    """Exit the script if an error was generated when executing the previous command."""

    variable_name: str | None = field(default=None)
    return_code: int | None = field(default=None)
    use_return_statement: bool = field(default=False, kw_only=True)

    # ----------------------------------------------------------------------
    def __post_init__(self) -> None:
        assert (
            (self.variable_name is None and self.return_code is None)
            or (self.variable_name is not None and self.return_code is None)
            or (self.variable_name is None and self.return_code is not None)
        ), (self.variable_name, self.return_code)


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class EchoOff(Command):
    """Disable printing of commands to the terminal."""


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class PersistError(Command):
    """Persist the current error value."""

    variable_name: str


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class PushDirectory(Command):
    """Push the current directory onto the directory stack and change to a new directory."""

    value: Path | None


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class PopDirectory(Command):
    """Pop a directory from the directory stack and change to that directory."""


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Raw(Command):
    """Raw, shell-specific content that isn't altered during decoration."""

    value: str
