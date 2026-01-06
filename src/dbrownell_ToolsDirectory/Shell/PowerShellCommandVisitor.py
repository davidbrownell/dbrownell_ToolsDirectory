# noqa: D100
import textwrap

from dbrownell_Common.Types import override

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
class PowerShellCommandVisitor(CommandVisitor):
    """Command visitor for PowerShell scripts."""

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self._message_substitution_lookup: dict[str, str] = {
            "`": "``",
            "$": "`$",
            '"': '`"',
        }

    # ----------------------------------------------------------------------
    @override
    def OnMessage(  # noqa: D102
        self,
        command: Message,
    ) -> str | None:
        output: list[str] = []

        for command_line in command.value.split("\n"):
            if not command_line.strip():
                output.append('Write-Host ""')
                continue

            line = command_line

            for source, dest in self._message_substitution_lookup.items():
                line = line.replace(source, dest)

            output.append(f'Write-Host "{line}"')

        return "; ".join(output) + "\n"

    # ----------------------------------------------------------------------
    @override
    def OnCall(  # noqa: D102
        self,
        command: Call,
    ) -> str | None:
        result = f". {command.command_line}\n"
        if command.exit_on_error:
            exit_on_error_result = self.Accept(
                ExitOnError(use_return_statement=command.exit_via_return_statement)
            )

            if exit_on_error_result:
                result += exit_on_error_result

        return result

    # ----------------------------------------------------------------------
    @override
    def OnExecute(  # noqa: D102
        self,
        command: Execute,
    ) -> str | None:
        result = f"& {command.command_line}\n"

        if command.exit_on_error:
            exit_on_error_result = self.Accept(
                ExitOnError(use_return_statement=command.exit_via_return_statement)
            )

            if exit_on_error_result:
                result += exit_on_error_result

        return result

    # ----------------------------------------------------------------------
    @override
    def OnSet(  # noqa: D102
        self,
        command: Set,
    ) -> str | None:
        if command.value_or_values is None:
            return f"Remove-Item Env:{command.name} -ErrorAction SilentlyContinue\n"

        values = ";".join(command.EnumValues())

        values = values.removeprefix('"')
        values = values.removesuffix('"')

        return f'$env:{command.name} = "{values}"\n'

    # ----------------------------------------------------------------------
    @override
    def OnAugment(  # noqa: D102
        self,
        command: Augment,
    ) -> str | None:
        statements: list[str] = []

        for value in command.EnumValues():
            if command.append_values:
                add_statement = f'$env:{command.name} = "$env:{command.name};{value}"'
            else:
                add_statement = f'$env:{command.name} = "{value};$env:{command.name}"'

            statement = textwrap.dedent(
                f"""\
                if (-not $env:{command.name} -or ";$env:{command.name};" -notlike "*;{value};*") {{
                    {add_statement}
                }}
                """,
            )

            statements.append(statement)

        return "".join(statements)

    # ----------------------------------------------------------------------
    @override
    def OnExit(  # noqa: D102
        self,
        command: Exit,
    ) -> str | None:
        return textwrap.dedent(
            """\
            {success}
            {error}
            exit {return_code}
            """,
        ).format(
            success=textwrap.dedent(
                """\
                if ($LASTEXITCODE -eq 0) {
                    Read-Host "Press [Enter] to continue"
                }
                """,
            ).rstrip()
            if command.pause_on_success
            else "",
            error=textwrap.dedent(
                """\
                if ($LASTEXITCODE -ne 0) {
                    Read-Host "Press [Enter] to continue"
                }
                """,
            ).rstrip()
            if command.pause_on_error
            else "",
            return_code=command.return_code or 0,
        )

    # ----------------------------------------------------------------------
    @override
    def OnExitOnError(  # noqa: D102
        self,
        command: ExitOnError,
    ) -> str | None:
        variable_name = f"${command.variable_name}" if command.variable_name else "$LASTEXITCODE"
        exit_keyword = "return" if command.use_return_statement else "exit"
        return_code = command.return_code if command.return_code is not None else "$error_code"

        return textwrap.dedent(
            f"""\
            $error_code = {variable_name}
            if ($error_code -ne 0) {{
                {exit_keyword} {return_code}
            }}
            """,
        )

    # ----------------------------------------------------------------------
    @override
    def OnEchoOff(  # noqa: D102
        self,
        command: EchoOff,  # noqa: ARG002
    ) -> str | None:
        # PowerShell doesn't echo commands by default
        return None

    # ----------------------------------------------------------------------
    @override
    def OnPersistError(  # noqa: D102
        self,
        command: PersistError,
    ) -> str | None:
        return f"${command.variable_name} = $LASTEXITCODE\n"

    # ----------------------------------------------------------------------
    @override
    def OnPushDirectory(  # noqa: D102
        self,
        command: PushDirectory,
    ) -> str | None:
        if command.value is None:
            return "Push-Location $PSScriptRoot\n"

        return f'Push-Location "{command.value}"\n'

    # ----------------------------------------------------------------------
    @override
    def OnPopDirectory(  # noqa: D102
        self,
        command: PopDirectory,  # noqa: ARG002
    ) -> str | None:
        return "Pop-Location\n"

    # ----------------------------------------------------------------------
    @override
    def OnRaw(  # noqa: D102
        self,
        command: Raw,
    ) -> str | None:
        return command.value.removesuffix("\n") + "\n"
