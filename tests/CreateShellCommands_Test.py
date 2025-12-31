from pathlib import Path

from dbrownell_ToolsDirectory.CreateShellCommands import CreateShellCommands
from dbrownell_ToolsDirectory.Shell.Commands import Augment, Command, EchoOff
from dbrownell_ToolsDirectory.ToolInfo import ToolInfo


# ----------------------------------------------------------------------
def test_Single() -> None:
    commands: list[Command] = CreateShellCommands(
        [
            ToolInfo(
                "the tool", Path("/some/tool"), Path("/some/tool/version"), Path("/some/tool/version/bin")
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/some/tool/version/bin"))),
    ]


# ----------------------------------------------------------------------
def test_Multiple() -> None:
    commands: list[Command] = CreateShellCommands(
        [
            ToolInfo(
                "tool A", Path("/some/toolA"), Path("/some/toolA/version"), Path("/some/toolA/version/bin")
            ),
            ToolInfo("tool B", Path("/some/toolB"), Path("/some/toolB/version"), Path("/some/toolB/version")),
            ToolInfo(
                "tool C", Path("/some/toolC"), Path("/some/toolC/version"), Path("/some/toolC/version/bin")
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/some/toolA/version/bin"))),
        Augment("PATH", str(Path("/some/toolB/version"))),
        Augment("PATH", str(Path("/some/toolC/version/bin"))),
    ]
