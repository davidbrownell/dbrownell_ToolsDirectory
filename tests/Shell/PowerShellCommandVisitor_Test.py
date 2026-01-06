import textwrap

from pathlib import Path

import pytest

from dbrownell_ToolsDirectory.Shell.Commands import *
from dbrownell_ToolsDirectory.Shell.PowerShellCommandVisitor import PowerShellCommandVisitor


# ----------------------------------------------------------------------
@pytest.mark.parametrize("special_char", ["`", "$", '"'])
def test_Message(special_char: str) -> None:
    if special_char == "`":
        escaped_char = "``"
    elif special_char == "$":
        escaped_char = "`$"
    else:
        escaped_char = '`"'

    command = PowerShellCommandVisitor().Accept(
        Message(
            textwrap.dedent(
                """\

                Line with special character: {}
                Next Line.

                The last line.
                """,
            ).format(special_char),
        ),
    )

    assert isinstance(command, str)

    # Break the command into lines so that we aren't fighting with ruff.
    lines = command.split("; ")

    assert len(lines) == 6

    assert lines[0] == 'Write-Host ""'
    assert lines[1] == f'Write-Host "Line with special character: {escaped_char}"'
    assert lines[2] == 'Write-Host "Next Line."'
    assert lines[3] == 'Write-Host ""'
    assert lines[4] == 'Write-Host "The last line."'
    assert lines[5] == 'Write-Host ""\n'


# ----------------------------------------------------------------------
class TestCall:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = PowerShellCommandVisitor().Accept(Call("script.ps1"))

        assert command == textwrap.dedent(
            """\
            . script.ps1
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                exit $error_code
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExitOnError(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Call(
                command_line="script.ps1",
                exit_on_error=False,
            ),
        )

        assert command == ". script.ps1\n"

    # ----------------------------------------------------------------------
    def test_ExitViaReturnStatement(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Call(
                command_line="script.ps1",
                exit_via_return_statement=True,
            ),
        )

        assert command == textwrap.dedent(
            """\
            . script.ps1
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                return $error_code
            }
            """,
        )


# ----------------------------------------------------------------------
class TestExecute:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = PowerShellCommandVisitor().Accept(Execute("myprogram.exe arg1 arg2"))

        assert command == textwrap.dedent(
            """\
            & myprogram.exe arg1 arg2
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                exit $error_code
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExitOnError(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Execute(
                command_line="myprogram.exe",
                exit_on_error=False,
            ),
        )

        assert command == "& myprogram.exe\n"

    # ----------------------------------------------------------------------
    def test_ExitViaReturnStatement(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Execute(
                command_line="myprogram.exe",
                exit_via_return_statement=True,
            ),
        )

        assert command == textwrap.dedent(
            """\
            & myprogram.exe
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                return $error_code
            }
            """,
        )


# ----------------------------------------------------------------------
class TestSet:
    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Set("MY_VAR", None),
        )

        assert command == "Remove-Item Env:MY_VAR -ErrorAction SilentlyContinue\n"

    # ----------------------------------------------------------------------
    def test_SingleValue(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Set("MY_VAR", "my_value"),
        )

        assert command == '$env:MY_VAR = "my_value"\n'

    # ----------------------------------------------------------------------
    def test_MultipleValues(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Set("MY_VAR", ["value1", "value2", "value3"]),
        )

        assert command == '$env:MY_VAR = "value1;value2;value3"\n'


# ----------------------------------------------------------------------
class TestAugment:
    # ----------------------------------------------------------------------
    def test_Single(self) -> None:
        command = PowerShellCommandVisitor().Accept(Augment("MY_VAR", "Value1"))

        assert isinstance(command, str)

        assert command == textwrap.dedent(
            """\
            if (-not $env:MY_VAR -or ";$env:MY_VAR;" -notlike "*;Value1;*") {
                $env:MY_VAR = "Value1;$env:MY_VAR"
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_Multiple(self) -> None:
        command = PowerShellCommandVisitor().Accept(Augment("MY_VAR", ["Value1", "Value2"]))

        assert isinstance(command, str)

        assert command == textwrap.dedent(
            """\
            if (-not $env:MY_VAR -or ";$env:MY_VAR;" -notlike "*;Value1;*") {
                $env:MY_VAR = "Value1;$env:MY_VAR"
            }
            if (-not $env:MY_VAR -or ";$env:MY_VAR;" -notlike "*;Value2;*") {
                $env:MY_VAR = "Value2;$env:MY_VAR"
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_AppendValues(self) -> None:
        command = PowerShellCommandVisitor().Accept(
            Augment("MY_VAR", ["Value1", "Value2"], append_values=True)
        )

        assert isinstance(command, str)

        assert command == textwrap.dedent(
            """\
            if (-not $env:MY_VAR -or ";$env:MY_VAR;" -notlike "*;Value1;*") {
                $env:MY_VAR = "$env:MY_VAR;Value1"
            }
            if (-not $env:MY_VAR -or ";$env:MY_VAR;" -notlike "*;Value2;*") {
                $env:MY_VAR = "$env:MY_VAR;Value2"
            }
            """,
        )


# ----------------------------------------------------------------------
class TestExit:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = PowerShellCommandVisitor().Accept(Exit())

        assert command == textwrap.dedent(
            """\


            exit 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnSuccess(self) -> None:
        command = PowerShellCommandVisitor().Accept(Exit(pause_on_success=True))

        assert command == textwrap.dedent(
            """\
            if ($LASTEXITCODE -eq 0) {
                Read-Host "Press [Enter] to continue"
            }

            exit 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnError(self) -> None:
        command = PowerShellCommandVisitor().Accept(Exit(pause_on_error=True))

        assert command == textwrap.dedent(
            """\

            if ($LASTEXITCODE -ne 0) {
                Read-Host "Press [Enter] to continue"
            }
            exit 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnCode(self) -> None:
        command = PowerShellCommandVisitor().Accept(Exit(return_code=5))

        assert command == textwrap.dedent(
            """\


            exit 5
            """,
        )


# ----------------------------------------------------------------------
class TestExitOnError:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = PowerShellCommandVisitor().Accept(ExitOnError())

        assert command == textwrap.dedent(
            """\
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                exit $error_code
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_CustomVariable(self) -> None:
        command = PowerShellCommandVisitor().Accept(ExitOnError(variable_name="MY_ERROR"))

        assert command == textwrap.dedent(
            """\
            $error_code = $MY_ERROR
            if ($error_code -ne 0) {
                exit $error_code
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnCode(self) -> None:
        command = PowerShellCommandVisitor().Accept(ExitOnError(return_code=10))

        assert command == textwrap.dedent(
            """\
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                exit 10
            }
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnStatement(self) -> None:
        command = PowerShellCommandVisitor().Accept(ExitOnError(use_return_statement=True))

        assert command == textwrap.dedent(
            """\
            $error_code = $LASTEXITCODE
            if ($error_code -ne 0) {
                return $error_code
            }
            """,
        )


# ----------------------------------------------------------------------
def test_EchoOff() -> None:
    command = PowerShellCommandVisitor().Accept(EchoOff())

    assert command is None


# ----------------------------------------------------------------------
def test_PersistError() -> None:
    command = PowerShellCommandVisitor().Accept(PersistError(variable_name="MY_ERROR"))

    assert command == "$MY_ERROR = $LASTEXITCODE\n"


# ----------------------------------------------------------------------
class TestPushDirectory:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = PowerShellCommandVisitor().Accept(PushDirectory(value=Path(r"C:\My\Directory")))

        assert command == 'Push-Location "C:\\My\\Directory"\n'

    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = PowerShellCommandVisitor().Accept(PushDirectory(value=None))

        assert command == "Push-Location $PSScriptRoot\n"


# ----------------------------------------------------------------------
def test_PopDirectory() -> None:
    command = PowerShellCommandVisitor().Accept(PopDirectory())

    assert command == "Pop-Location\n"


# ----------------------------------------------------------------------
def test_Raw() -> None:
    command = PowerShellCommandVisitor().Accept(Raw("some raw command"))

    assert command == "some raw command\n"
