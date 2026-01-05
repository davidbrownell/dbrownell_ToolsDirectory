import textwrap

from pathlib import Path

import pytest

from dbrownell_ToolsDirectory.Shell.BashCommandVisitor import BashCommandVisitor
from dbrownell_ToolsDirectory.Shell.Commands import *


# ----------------------------------------------------------------------
@pytest.mark.parametrize("special_char", ["$", '"', "`"])
def test_Message(special_char: str) -> None:
    escaped_char = r"\\\`" if special_char == "`" else rf"\{special_char}"

    command = BashCommandVisitor().Accept(
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
    lines = command.split(" && ")

    assert len(lines) == 6

    assert lines[0] == 'echo ""'
    assert lines[1] == f'echo "Line with special character: {escaped_char}"'
    assert lines[2] == 'echo "Next Line."'
    assert lines[3] == 'echo ""'
    assert lines[4] == 'echo "The last line."'
    assert lines[5] == 'echo ""\n'


# ----------------------------------------------------------------------
class TestCall:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = BashCommandVisitor().Accept(Call("the command"))

        assert command == textwrap.dedent(
            """\
            source the command
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                exit $error_code
            fi
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExitOnError(self) -> None:
        command = BashCommandVisitor().Accept(
            Call(
                command_line="the command",
                exit_on_error=False,
            ),
        )

        assert command == "source the command\n"

    # ----------------------------------------------------------------------
    def test_ExitViaReturnStatement(self) -> None:
        command = BashCommandVisitor().Accept(
            Call(
                command_line="the command",
                exit_via_return_statement=True,
            ),
        )

        assert command == textwrap.dedent(
            """\
            source the command
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                return $error_code
            fi
            """,
        )


# ----------------------------------------------------------------------
class TestExecute:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = BashCommandVisitor().Accept(Execute("the command"))

        assert command == textwrap.dedent(
            """\
            the command
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                exit $error_code
            fi
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExitOnError(self) -> None:
        command = BashCommandVisitor().Accept(
            Execute(
                command_line="the command",
                exit_on_error=False,
            ),
        )

        assert command == "the command\n"

    # ----------------------------------------------------------------------
    def test_ExitViaReturnStatement(self) -> None:
        command = BashCommandVisitor().Accept(
            Execute(
                command_line="the command",
                exit_via_return_statement=True,
            ),
        )

        assert command == textwrap.dedent(
            """\
            the command
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                return $error_code
            fi
            """,
        )


# ----------------------------------------------------------------------
class TestSet:
    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = BashCommandVisitor().Accept(
            Set("MY_VAR", None),
        )

        assert command == "unset MY_VAR\n"

    # ----------------------------------------------------------------------
    def test_SingleValue(self) -> None:
        command = BashCommandVisitor().Accept(
            Set("MY_VAR", "my_value"),
        )

        assert command == 'export MY_VAR="my_value"\n'

    # ----------------------------------------------------------------------
    def test_MultipleValues(self) -> None:
        command = BashCommandVisitor().Accept(
            Set("MY_VAR", ["value1", "value2", "value3"]),
        )

        assert command == 'export MY_VAR="value1:value2:value3"\n'


# ----------------------------------------------------------------------
class TestAugment:
    # ----------------------------------------------------------------------
    def test_Single(self) -> None:
        command = BashCommandVisitor().Accept(Augment("MY_VAR", "Value1"))

        assert command == textwrap.dedent(
            """\
            [[ ":${MY_VAR}:" != *":Value1:"* ]] && export MY_VAR="${MY_VAR}:Value1"
            true
            """,
        )

    # ----------------------------------------------------------------------
    def test_Multiple(self) -> None:
        command = BashCommandVisitor().Accept(Augment("MY_VAR", ["Value1", "Value2", "Value3"]))

        assert command == textwrap.dedent(
            """\
            [[ ":${MY_VAR}:" != *":Value1:"* ]] && export MY_VAR="${MY_VAR}:Value1"
            true
            [[ ":${MY_VAR}:" != *":Value2:"* ]] && export MY_VAR="${MY_VAR}:Value2"
            true
            [[ ":${MY_VAR}:" != *":Value3:"* ]] && export MY_VAR="${MY_VAR}:Value3"
            true
            """,
        )

    # ----------------------------------------------------------------------
    def test_AppendValues(self) -> None:
        command = BashCommandVisitor().Accept(Augment("MY_VAR", ["Value1", "Value2"], append_values=True))

        assert command == textwrap.dedent(
            """\
            [[ ":${MY_VAR}:" != *":Value1:"* ]] && export MY_VAR="Value1:${MY_VAR}"
            true
            [[ ":${MY_VAR}:" != *":Value2:"* ]] && export MY_VAR="Value2:${MY_VAR}"
            true
            """,
        )


# ----------------------------------------------------------------------
class TestExit:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BashCommandVisitor().Accept(Exit())

        assert command == textwrap.dedent(
            """\


            return 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnSuccess(self) -> None:
        command = BashCommandVisitor().Accept(Exit(pause_on_success=True))

        assert command == textwrap.dedent(
            """\
            if [[ $? -eq 0 ]]; then
                read -p "Press [Enter] to continue"
            fi

            return 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnError(self) -> None:
        command = BashCommandVisitor().Accept(Exit(pause_on_error=True))

        assert command == textwrap.dedent(
            """\

            if [[ $? -ne 0 ]]; then
                read -p "Press [Enter] to continue"
            fi
            return 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnCode(self) -> None:
        command = BashCommandVisitor().Accept(Exit(return_code=5))

        assert command == textwrap.dedent(
            """\


            return 5
            """,
        )


# ----------------------------------------------------------------------
class TestExitOnError:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BashCommandVisitor().Accept(ExitOnError())

        assert command == textwrap.dedent(
            """\
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                exit $error_code
            fi
            """,
        )

    # ----------------------------------------------------------------------
    def test_CustomVariable(self) -> None:
        command = BashCommandVisitor().Accept(ExitOnError(variable_name="MY_ERROR"))

        assert command == textwrap.dedent(
            """\
            error_code=$MY_ERROR
            if [[ $error_code -ne 0 ]]; then
                exit $error_code
            fi
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnStatement(self) -> None:
        command = BashCommandVisitor().Accept(ExitOnError(use_return_statement=True))

        assert command == textwrap.dedent(
            """\
            error_code=$?
            if [[ $error_code -ne 0 ]]; then
                return $error_code
            fi
            """,
        )


# ----------------------------------------------------------------------
def test_EchoOff() -> None:
    command = BashCommandVisitor().Accept(EchoOff())

    assert command == textwrap.dedent(
        """\
        set +v
        set +x

        """,
    )


# ----------------------------------------------------------------------
def test_PersistError() -> None:
    command = BashCommandVisitor().Accept(PersistError(variable_name="MY_ERROR"))

    assert command == "MY_ERROR=$?\n"


# ----------------------------------------------------------------------
class TestPushDirectory:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BashCommandVisitor().Accept(PushDirectory(value=Path("/my/dir")))

        assert command == textwrap.dedent(
            """\
            pushd "/my/dir" > /dev/null
            """,
        )

    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = BashCommandVisitor().Accept(PushDirectory(value=None))

        assert command == textwrap.dedent(
            """\
            pushd $( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd ) > /dev/null
            """,
        )


# ----------------------------------------------------------------------
def test_PopDirectory() -> None:
    command = BashCommandVisitor().Accept(PopDirectory())

    assert command == textwrap.dedent(
        """\
        popd > /dev/null
        """,
    )


# ----------------------------------------------------------------------
def test_Raw() -> None:
    command = BashCommandVisitor().Accept(Raw("some raw command"))

    assert command == "some raw command\n"
