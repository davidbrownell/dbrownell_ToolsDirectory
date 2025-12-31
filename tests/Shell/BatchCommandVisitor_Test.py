import re
import textwrap

from pathlib import Path

import pytest

from dbrownell_ToolsDirectory.Shell.Commands import *
from dbrownell_ToolsDirectory.Shell.BatchCommandVisitor import BatchCommandVisitor


# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "special_char",
    [
        "%",
        "&",
        "<",
        ">",
        "|",
        ",",
        ";",
        "(",
        ")",
        "[",
        "]",
    ],
)
def test_Message(special_char) -> None:
    escaped_char = "%%" if special_char == "%" else f"^{special_char}"

    command = BatchCommandVisitor().Accept(
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

    # Break the command into lines so that we can look for trailing whitespace (this would be
    # removed by the editor if we checked everything at once).
    lines = command.split(" && ")

    assert len(lines) == 6

    assert lines[0] == "echo. "
    assert lines[1] == f"echo Line with special character: {escaped_char}"
    assert lines[2] == "echo Next Line."
    assert lines[3] == "echo. "
    assert lines[4] == "echo The last line."
    assert lines[5] == "echo. \n"


# ----------------------------------------------------------------------
class TestCall:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = BatchCommandVisitor().Accept(Call("the command"))

        assert command == textwrap.dedent(
            """\
            call the command
            if %ERRORLEVEL% NEQ 0 (exit /B %ERRORLEVEL%)
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExit(self) -> None:
        command = BatchCommandVisitor().Accept(
            Call(
                command_line="the command",
                exit_on_error=False,
            ),
        )

        assert command == "call the command\n"


# ----------------------------------------------------------------------
class TestExecute:
    # ----------------------------------------------------------------------
    def test_Default(self) -> None:
        command = BatchCommandVisitor().Accept(Execute('the command arg1 "with complex args" arg2'))

        assert command == textwrap.dedent(
            """\
            the command arg1 "with complex args" arg2
            if %ERRORLEVEL% NEQ 0 (exit /B %ERRORLEVEL%)
            """,
        )

    # ----------------------------------------------------------------------
    def test_NoExit(self) -> None:
        command = BatchCommandVisitor().Accept(
            Execute(
                command_line="the command",
                exit_on_error=False,
            ),
        )

        assert command == "the command\n"

    # ----------------------------------------------------------------------
    @pytest.mark.parametrize("script_extension", [".bat", ".cmd"])
    def test_Script(self, script_extension) -> None:
        command = BatchCommandVisitor().Accept(
            Execute(
                command_line=f"myscript{script_extension} arg1 arg2",
            ),
        )

        assert command == textwrap.dedent(
            """\
            cmd /c myscript{} arg1 arg2
            if %ERRORLEVEL% NEQ 0 (exit /B %ERRORLEVEL%)
            """.format(
                script_extension,
            ),
        )


# ----------------------------------------------------------------------
class TestSet:
    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = BatchCommandVisitor().Accept(
            Set(
                name="MyVar",
                value_or_values=None,
            ),
        )

        assert command == "SET MyVar=\n"

    # ----------------------------------------------------------------------
    def test_SingleValue(self) -> None:
        command = BatchCommandVisitor().Accept(
            Set(
                name="MyVar",
                value_or_values="MyValue",
            ),
        )

        assert command == "SET MyVar=MyValue\n"

    # ----------------------------------------------------------------------
    def test_MultipleValues(self) -> None:
        command = BatchCommandVisitor().Accept(
            Set(
                name="MyVar",
                value_or_values=["Value1", "Value2", "Value3"],
            ),
        )

        assert command == "SET MyVar=Value1;Value2;Value3\n"


# ----------------------------------------------------------------------
class TestAugment:
    # ----------------------------------------------------------------------
    def test_Single(self) -> None:
        command = BatchCommandVisitor().Accept(
            Augment(
                name="MyVar",
                value_or_values="Value1",
            ),
        )

        assert isinstance(command, str)

        assert self._Scrub(command) == textwrap.dedent(
            """\
            REM Value1
            echo ";%MyVar%;" | findstr /C:";Value1;" >nul
            if %ERRORLEVEL% == 0 goto skip_<UNIQUE_ID_1>

            SET MyVar=%MyVar%;Value1

            :skip_<UNIQUE_ID_1>

            """,
        )

    # ----------------------------------------------------------------------
    def test_Multiple(self) -> None:
        command = BatchCommandVisitor().Accept(
            Augment(
                name="MyVar",
                value_or_values=["ValueA", "ValueB"],
            ),
        )

        assert isinstance(command, str)

        assert self._Scrub(command) == textwrap.dedent(
            """\
            REM ValueA
            echo ";%MyVar%;" | findstr /C:";ValueA;" >nul
            if %ERRORLEVEL% == 0 goto skip_<UNIQUE_ID_1>

            SET MyVar=%MyVar%;ValueA

            :skip_<UNIQUE_ID_1>

            REM ValueB
            echo ";%MyVar%;" | findstr /C:";ValueB;" >nul
            if %ERRORLEVEL% == 0 goto skip_<UNIQUE_ID_2>

            SET MyVar=%MyVar%;ValueB

            :skip_<UNIQUE_ID_2>

            """,
        )

    # ----------------------------------------------------------------------
    def test_AppendValues(self) -> None:
        command = BatchCommandVisitor().Accept(
            Augment(
                name="MyVar",
                value_or_values=["ValueA", "ValueB"],
                append_values=True,
            ),
        )

        assert isinstance(command, str)

        assert self._Scrub(command) == textwrap.dedent(
            """\
            REM ValueA
            echo ";%MyVar%;" | findstr /C:";ValueA;" >nul
            if %ERRORLEVEL% == 0 goto skip_<UNIQUE_ID_1>

            SET MyVar=ValueA;%MyVar%

            :skip_<UNIQUE_ID_1>

            REM ValueB
            echo ";%MyVar%;" | findstr /C:";ValueB;" >nul
            if %ERRORLEVEL% == 0 goto skip_<UNIQUE_ID_2>

            SET MyVar=ValueB;%MyVar%

            :skip_<UNIQUE_ID_2>

            """,
        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Scrub(value: str) -> str:
        id_lookup: dict[str, str] = {}

        # ----------------------------------------------------------------------
        def Replace(match: re.Match[str]) -> str:
            the_id = match.group("id")

            if the_id not in id_lookup:
                id_lookup[the_id] = f"<UNIQUE_ID_{len(id_lookup) + 1}>"

            return id_lookup[the_id]

        # ----------------------------------------------------------------------

        return re.sub(r"(?P<id>[0-9A-Fa-f]{32})", Replace, value)


# ----------------------------------------------------------------------
class TestExit:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BatchCommandVisitor().Accept(Exit())

        assert command == textwrap.dedent(
            """\


            exit /B 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnSuccess(self) -> None:
        command = BatchCommandVisitor().Accept(
            Exit(
                pause_on_success=True,
            ),
        )

        assert command == textwrap.dedent(
            """\
            if %ERRORLEVEL% EQ 0 (pause)

            exit /B 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_PauseOnError(self) -> None:
        command = BatchCommandVisitor().Accept(Exit(pause_on_error=True))

        assert command == textwrap.dedent(
            """\

            if %ERRORLEVEL% NEQ 0 (pause)
            exit /B 0
            """,
        )

    # ----------------------------------------------------------------------
    def test_ReturnCode(self) -> None:
        command = BatchCommandVisitor().Accept(Exit(return_code=5))

        assert command == textwrap.dedent(
            """\


            exit /B 5
            """,
        )


# ----------------------------------------------------------------------
class TestExitOnError:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BatchCommandVisitor().Accept(ExitOnError())

        assert command == "if %ERRORLEVEL% NEQ 0 (exit /B %ERRORLEVEL%)\n"

    # ----------------------------------------------------------------------
    def test_CustomVariable(self) -> None:
        command = BatchCommandVisitor().Accept(ExitOnError("MY_ERROR_VAR"))

        assert command == "if %MY_ERROR_VAR% NEQ 0 (exit /B %MY_ERROR_VAR%)\n"

    # ----------------------------------------------------------------------
    def test_ReturnCode(self) -> None:
        command = BatchCommandVisitor().Accept(ExitOnError(return_code=10))

        assert command == "if %ERRORLEVEL% NEQ 0 (exit /B 10)\n"


# ----------------------------------------------------------------------
def test_EchoOff() -> None:
    command = BatchCommandVisitor().Accept(EchoOff())

    assert command == "@echo off\n\n"


# ----------------------------------------------------------------------
def test_PersistError() -> None:
    command = BatchCommandVisitor().Accept(PersistError("MY_ERROR_VAR"))

    assert command == "SET MY_ERROR_VAR=%ERRORLEVEL%\n"


# ----------------------------------------------------------------------
class TestPushDirectory:
    # ----------------------------------------------------------------------
    def test_Standard(self) -> None:
        command = BatchCommandVisitor().Accept(PushDirectory(Path(r"C:\My\Directory")))

        assert command == 'pushd "C:\\My\\Directory"\n'

    # ----------------------------------------------------------------------
    def test_None(self) -> None:
        command = BatchCommandVisitor().Accept(PushDirectory(None))

        assert command == 'pushd "%~dp0"\n'


# ----------------------------------------------------------------------
def test_PopDirectory() -> None:
    command = BatchCommandVisitor().Accept(PopDirectory())

    assert command == "popd\n"


# ----------------------------------------------------------------------
def test_Raw() -> None:
    command = BatchCommandVisitor().Accept(Raw("This is a raw command"))

    assert command == "This is a raw command\n"
