# noqa: D100
from typing import TYPE_CHECKING

from dbrownell_ToolsDirectory.Shell.Commands import Augment, Command, EchoOff

if TYPE_CHECKING:
    from dbrownell_ToolsDirectory.ToolInfo import ToolInfo


# ----------------------------------------------------------------------
def CreateShellCommands(
    tool_infos: list[ToolInfo],
) -> list[Command]:
    """Create shell commands to set up the environment for the specified tools."""

    commands: list[Command] = [EchoOff()]

    for tool_info in tool_infos:
        commands.append(Augment("PATH", str(tool_info.binary_directory)))  # noqa: PERF401

        # TODO: Search for and apply environment files

    return commands
