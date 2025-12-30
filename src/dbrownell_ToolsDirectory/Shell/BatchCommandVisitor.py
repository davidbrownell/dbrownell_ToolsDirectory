# noqa: D100
import shlex
import textwrap
import uuid

from dbrownell_ToolsDirectory.Shell.Commands import (
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
from dbrownell_ToolsDirectory.Shell.CommandVisitor import CommandVisitor


# ----------------------------------------------------------------------
class BatchCommandVisitor(CommandVisitor):
    """Command visitor for Windows batch scripts."""

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self._message_substitution_lookup: dict[str, str] = {
            "%": "%%",
            "&": "^&",
            "<": "^<",
            ">": "^>",
            "|": "^|",
            ",": "^,",
            ";": "^;",
            "(": "^(",
            ")": "^)",
            "[": "^[",
            "]": "^]",
        }

    # ----------------------------------------------------------------------
    def OnMessage(  # noqa: D102
        self,
        command: Message,
    ) -> str | None:
        output: list[str] = []

        for command_line in command.value.split("\n"):
            if not command_line.strip():
                # Note that the trailing white space seems to be necessary on some terminals
                output.append("echo. ")
                continue

            line = command_line.replace("^", "__caret_placeholder__")

            for source, dest in self._message_substitution_lookup.items():
                line = line.replace(source, dest)

            line = line.replace("__caret_placeholder__", "^")

            output.append(f"echo {line}")

        return " && ".join(output)

    # ----------------------------------------------------------------------
    def OnCall(  # noqa: D102
        self,
        command: Call,
    ) -> str | None:
        result = f"call {command.command_line}"
        if command.exit_on_error:
            result += "\n{}\n".format(self.Accept(ExitOnError()))

        return result

    # ----------------------------------------------------------------------
    def OnExecute(  # noqa: D102
        self,
        command: Execute,
    ) -> str | None:
        commands: list[str] = shlex.split(command.command_line)

        if commands[0].lower().endswith((".bat", ".cmd")):
            result = f"cmd /c {command.command_line}"
        else:
            result = command.command_line

        if command.exit_on_error:
            result += "\n{}\n".format(self.Accept(ExitOnError()))

        return result

    # ----------------------------------------------------------------------
    def OnSet(  # noqa: D102
        self,
        command: Set,
    ) -> str | None:
        if command.value_or_values is None:
            return f"SET {command.name}="

        return f"SET {command.name}={';'.join(command.EnumValues())}"

    # ----------------------------------------------------------------------
    def OnAugment(  # noqa: D102
        self,
        command: Augment,
    ) -> str | None:
        if command.append_values:
            add_statement_template = f"{{value}};%{command.name}%"
        else:
            add_statement_template = f"%{command.name}%;{{value}}"

        statement_template = textwrap.dedent(
            """\
            REM {{value}}
            echo ";%{name}%;" | findstr /C:";{{value}};" >nul
            if %ERRORLEVEL% EQ 0 goto skip_{{unique_id}}

            SET {name}={add_statement_template}

            :skip_{{unique_id}}

            """,
        ).format(
            name=command.name,
            add_statement_template=add_statement_template,
        )

        statements: list[str] = [
            statement_template.format(
                value=value,
                unique_id=str(uuid.uuid4()).replace("-", ""),
            )
            for value in command.EnumValues()
        ]

        return "".join(statements)

    # ----------------------------------------------------------------------
    def OnExit(  # noqa: D102
        self,
        command: Exit,
    ) -> str | None:
        return textwrap.dedent(
            """\
            {success}
            {error}
            exit /B {return_code}
            """,
        ).format(
            success="if %ERRORLEVEL% EQ 0 (pause)" if command.pause_on_success else "",
            error="if %ERRORLEVEL% NEQ 0 (pause)" if command.pause_on_error else "",
            return_code=command.return_code or 0,
        )

    # ----------------------------------------------------------------------
    def OnExitOnError(  # noqa: D102
        self,
        command: ExitOnError,
    ) -> str | None:
        variable_name = command.variable_name or "ERRORLEVEL"

        return "if %{}% NEQ 0 (exit /B {})".format(
            variable_name,
            command.return_code if command.return_code is not None else f"%{variable_name}%",
        )

    # ----------------------------------------------------------------------
    def OnEchoOff(  # noqa: D102
        self,
        command: EchoOff,  # noqa: ARG002
    ) -> str | None:
        return "@echo off"

    # ----------------------------------------------------------------------
    def OnPersistError(  # noqa: D102
        self,
        command: PersistError,
    ) -> str | None:
        return f"SET {command.variable_name}=%ERRORLEVEL%"

    # ----------------------------------------------------------------------
    def OnPushDirectory(  # noqa: D102
        self,
        command: PushDirectory,
    ) -> str | None:
        directory = command.value or "%~dp0"
        return f'pushd "{directory}"'

    # ----------------------------------------------------------------------
    def OnPopDirectory(  # noqa: D102
        self,
        command: PopDirectory,  # noqa: ARG002
    ) -> str | None:
        return "popd"

    # ----------------------------------------------------------------------
    def OnRaw(  # noqa: D102
        self,
        command: Raw,
    ) -> str | None:
        return command.value
