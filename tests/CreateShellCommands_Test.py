import os
import textwrap

from pathlib import Path

from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from semantic_version import Version as SemVer

from dbrownell_ToolsDirectory.CreateShellCommands import CreateShellCommands
from dbrownell_ToolsDirectory.Shell.Commands import Augment, Command, EchoOff, Raw, Set
from dbrownell_ToolsDirectory.ToolInfo import ToolInfo


# ----------------------------------------------------------------------
def test_Single() -> None:
    dm_and_sink = iter(GenerateDoneManagerAndContent())

    commands: list[Command] = CreateShellCommands(
        next(dm_and_sink),
        [
            ToolInfo(
                "the tool",
                None,
                None,
                None,
                Path("/some/tool"),
                Path("/some/tool/version"),
                Path("/some/tool/version/bin"),
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/some/tool/version/bin"))),
    ]


# ----------------------------------------------------------------------
def test_Multiple() -> None:
    dm_and_sink = iter(GenerateDoneManagerAndContent())

    commands: list[Command] = CreateShellCommands(
        next(dm_and_sink),
        [
            ToolInfo(
                "tool A",
                None,
                None,
                None,
                Path("/some/toolA"),
                Path("/some/toolA/version"),
                Path("/some/toolA/version/bin"),
            ),
            ToolInfo(
                "tool B",
                None,
                None,
                None,
                Path("/some/toolB"),
                Path("/some/toolB/version"),
                Path("/some/toolB/version"),
            ),
            ToolInfo(
                "tool C",
                None,
                None,
                None,
                Path("/some/toolC"),
                Path("/some/toolC/version"),
                Path("/some/toolC/version/bin"),
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/some/toolA/version/bin"))),
        Augment("PATH", str(Path("/some/toolB/version"))),
        Augment("PATH", str(Path("/some/toolC/version/bin"))),
    ]


# ----------------------------------------------------------------------
def test_EnvFiles(fs) -> None:
    fs.create_file(
        "/tools/Tool1/Tool1.env",
        contents=textwrap.dedent(
            """\
            VALUE1=1
            VALUE2=2
            SPECIAL_VALUE=original_value
            RELATIVE_PATH1=./path1

            UNSET_VALUE=
            """,
        ),
    )

    fs.create_file(
        "/tools/Tool1/1.0.0/Tool1.env",
        contents=textwrap.dedent(
            """\
            VALUE3=3
            SPECIAL_VALUE=overridden_value
            VALUE4=4
            RELATIVE_PATH2=./path2
            """,
        ),
    )

    dm_and_sink = iter(GenerateDoneManagerAndContent())

    commands: list[Command] = CreateShellCommands(
        next(dm_and_sink),
        [
            ToolInfo(
                "Tool1",
                SemVer("1.0.0"),
                None,
                None,
                Path("/tools/Tool1"),
                Path("/tools/Tool1/1.0.0"),
                Path("/tools/Tool1/1.0.0/bin"),
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/tools/Tool1/1.0.0/bin"))),
        Set("VALUE1", "1"),
        Set("VALUE2", "2"),
        Set("SPECIAL_VALUE", "overridden_value"),
        Set("RELATIVE_PATH1", str(Path("/tools/Tool1/path1"))),
        Set("UNSET_VALUE", ""),
        Set("VALUE3", "3"),
        Set("VALUE4", "4"),
        Set("RELATIVE_PATH2", str(Path("/tools/Tool1/1.0.0/path2"))),
        Raw("\n"),
    ]

    assert "DONE! (0, <scrubbed duration>)" in next(dm_and_sink)


# ----------------------------------------------------------------------
def test_EnvFilesInvalidContent(fs) -> None:
    fs.create_file(
        "/tools/Tool1/Tool1.env",
        contents=textwrap.dedent(
            """\
            VALUE1=1
            INVALID LINE
            VALUE2=2
            """,
        ),
    )

    dm_and_sink = iter(GenerateDoneManagerAndContent())

    commands: list[Command] = CreateShellCommands(
        next(dm_and_sink),
        [
            ToolInfo(
                "Tool1",
                None,
                None,
                None,
                Path("/tools/Tool1"),
                Path("/tools/Tool1/version"),
                Path("/tools/Tool1/version/bin"),
            ),
        ],
    )

    assert commands == [
        EchoOff(),
        Augment("PATH", str(Path("/tools/Tool1/version/bin"))),
    ]

    assert next(dm_and_sink) == textwrap.dedent(
        """\
        Heading...
          Creating shell commands...
            ERROR: Unable to process the environment file '{sep}tools{sep}Tool1{sep}Tool1.env': python-dotenv could not parse statement starting at line 2
          DONE! (-1, <scrubbed duration>)
        DONE! (-1, <scrubbed duration>)
        """,
    ).format(sep=os.path.sep)
