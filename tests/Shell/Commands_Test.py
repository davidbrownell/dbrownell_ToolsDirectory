from unittest.mock import Mock

from dbrownell_ToolsDirectory.Shell.Commands import *


# ----------------------------------------------------------------------
def test_Message() -> None:
    value = Mock()

    command = Message(value)

    assert command.value is value


# ----------------------------------------------------------------------
def test_Call() -> None:
    command_line = Mock()
    exit_on_error = Mock()
    exit_via_return_statement = Mock()

    command = Call(
        command_line=command_line,
        exit_on_error=exit_on_error,  # ty: ignore[invalid-argument-type]
        exit_via_return_statement=exit_via_return_statement,  # ty: ignore[invalid-argument-type]
    )

    assert command.command_line is command_line
    assert command.exit_on_error is exit_on_error
    assert command.exit_via_return_statement is exit_via_return_statement


# ----------------------------------------------------------------------
def test_Execute() -> None:
    command_line = Mock()
    exit_on_error = Mock()
    exit_via_return_statement = Mock()

    command = Execute(
        command_line=command_line,
        exit_on_error=exit_on_error,  # ty: ignore[invalid-argument-type]
        exit_via_return_statement=exit_via_return_statement,  # ty: ignore[invalid-argument-type]
    )

    assert command.command_line is command_line
    assert command.exit_on_error is exit_on_error
    assert command.exit_via_return_statement is exit_via_return_statement


# ----------------------------------------------------------------------
class TestSet:
    # ----------------------------------------------------------------------
    def test_Create(self) -> None:
        name = Mock()
        value_or_values = Mock()

        command = Set(
            name=name,
            value_or_values=value_or_values,
        )

        assert command.name is name
        assert command.value_or_values is value_or_values

    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        assert list(Set("TheSet", None).EnumValues()) == []

    # ----------------------------------------------------------------------
    def test_SingleValue(self) -> None:
        assert list(Set("TheSet", "Value").EnumValues()) == ["Value"]

    # ----------------------------------------------------------------------
    def test_MultipleValues(self) -> None:
        assert list(Set("TheSet", ["Value1", "Value2"]).EnumValues()) == [
            "Value1",
            "Value2",
        ]


# ----------------------------------------------------------------------
class TestArgument:
    # ----------------------------------------------------------------------
    def test_Create(self) -> None:
        name = Mock()
        value_or_values = Mock()
        append_values = Mock()

        command = Augment(
            name=name,
            value_or_values=value_or_values,
            append_values=append_values,  # ty: ignore[invalid-argument-type]
        )

        assert command.name is name
        assert command.value_or_values is value_or_values
        assert command.append_values is append_values

    # ----------------------------------------------------------------------
    def test_SingleValue(self) -> None:
        assert list(Augment("TheSet", "Value").EnumValues()) == ["Value"]

    # ----------------------------------------------------------------------
    def test_MultipleValues(self) -> None:
        assert list(Augment("TheSet", ["Value1", "Value2"]).EnumValues()) == [
            "Value1",
            "Value2",
        ]


# ----------------------------------------------------------------------
def test_Exit() -> None:
    pause_on_success = Mock()
    pause_on_error = Mock()
    return_code = Mock()

    command = Exit(
        pause_on_success=pause_on_success,  # ty: ignore[invalid-argument-type]
        pause_on_error=pause_on_error,  # ty: ignore[invalid-argument-type]
        return_code=return_code,  # ty: ignore[invalid-argument-type]
    )

    assert command.pause_on_success is pause_on_success
    assert command.pause_on_error is pause_on_error
    assert command.return_code is return_code


# ----------------------------------------------------------------------
def test_ExitOnError() -> None:
    variable_name = Mock()
    use_return_statement = Mock()

    command = ExitOnError(
        variable_name=variable_name,  # ty: ignore[invalid-argument-type]
        return_code=None,
        use_return_statement=use_return_statement,  # ty: ignore[invalid-argument-type]
    )

    assert command.variable_name is variable_name
    assert command.return_code is None
    assert command.use_return_statement is use_return_statement


# ----------------------------------------------------------------------
def test_EchoOff() -> None:
    command = EchoOff()

    assert isinstance(command, EchoOff)


# ----------------------------------------------------------------------
def test_PersistError() -> None:
    variable_name = Mock()

    command = PersistError(
        variable_name=variable_name,  # ty: ignore[invalid-argument-type]
    )

    assert command.variable_name is variable_name


# ----------------------------------------------------------------------
def test_PushDirectory() -> None:
    value = Mock()

    command = PushDirectory(
        value=value,  # ty: ignore[invalid-argument-type]
    )

    assert command.value is value


# ----------------------------------------------------------------------
def test_PopDirectory() -> None:
    command = PopDirectory()

    assert isinstance(command, PopDirectory)


# ----------------------------------------------------------------------
def test_Raw() -> None:
    value = Mock()

    command = Raw(
        value=value,  # ty: ignore[invalid-argument-type]
    )

    assert command.value is value
