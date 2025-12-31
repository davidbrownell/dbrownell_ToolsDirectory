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
class BashCommandVisitor(CommandVisitor):
    """Command visitor for Linux bash scripts."""

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self._message_substitution_lookup: dict[str, str] = {
            "$": r"\$",
            '"': r"\"",
            "`": r"\\\`",
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
                output.append('echo ""')
                continue

            line = command_line

            for source, dest in self._message_substitution_lookup.items():
                line = line.replace(source, dest)

            output.append(f'echo "{line}"')

        return " && ".join(output) + "\n"

    # ----------------------------------------------------------------------
    @override
    def OnCall(  # noqa: D102
        self,
        command: Call,
    ) -> str | None:
        result = f"source {command.command_line}\n"
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
        result = command.command_line + "\n"

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
            return f"unset {command.name}\n"

        values = ":".join(command.EnumValues())

        values = values.removeprefix('"')
        values = values.removesuffix('"')

        return f'export {command.name}="{values}"\n'

    # ----------------------------------------------------------------------
    @override
    def OnAugment(  # noqa: D102
        self,
        command: Augment,
    ) -> str | None:
        if command.append_values:
            add_statement_template = f"{{value}}:${{{{{command.name}}}}}"
        else:
            add_statement_template = f"${{{{{command.name}}}}}:{{value}}"

        add_statement_template = f'export {command.name}="{add_statement_template}"'

        statement_template = (
            f'[[ ":${{{{{command.name}}}}}:" != *":{{value}}:"* ]] && ' + add_statement_template
        )

        statements: list[str] = [statement_template.format(value=value) for value in command.EnumValues()]

        return "\n".join(statements) + "\n"

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
            return {return_code}
            """,
        ).format(
            success=textwrap.dedent(
                """\
                if [[ $? -eq 0 ]]; then
                    read -p "Press [Enter] to continue"
                fi
                """,
            ).rstrip()
            if command.pause_on_success
            else "",
            error=textwrap.dedent(
                """\
                if [[ $? -ne 0 ]]; then
                    read -p "Press [Enter] to continue"
                fi
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
        variable_name = f"${command.variable_name}" if command.variable_name else "$?"

        return textwrap.dedent(
            f"""\
            error_code={variable_name}
            if [[ $error_code -ne 0 ]]; then
                {"return" if command.use_return_statement else "exit"} {command.return_code or "$error_code"}
            fi
            """,
        )

    # ----------------------------------------------------------------------
    @override
    def OnEchoOff(  # noqa: D102
        self,
        command: EchoOff,  # noqa: ARG002
    ) -> str | None:
        return "set +x\n\n"

    # ----------------------------------------------------------------------
    @override
    def OnPersistError(  # noqa: D102
        self,
        command: PersistError,
    ) -> str | None:
        return f"{command.variable_name}=$?\n"

    # ----------------------------------------------------------------------
    @override
    def OnPushDirectory(  # noqa: D102
        self,
        command: PushDirectory,
    ) -> str | None:
        if command.value is None:
            directory = """$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"""
        else:
            directory = f'"{command.value.as_posix()}"'

        return f"pushd {directory} > /dev/null\n"

    # ----------------------------------------------------------------------
    @override
    def OnPopDirectory(  # noqa: D102
        self,
        command: PopDirectory,  # noqa: ARG002
    ) -> str | None:
        return "popd > /dev/null\n"

    # ----------------------------------------------------------------------
    @override
    def OnRaw(  # noqa: D102
        self,
        command: Raw,
    ) -> str | None:
        return command.value.removesuffix("\n") + "\n"
