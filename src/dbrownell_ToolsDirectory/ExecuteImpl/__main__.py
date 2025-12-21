# noqa: D100
import re
import textwrap

from enum import Enum
from pathlib import Path  # noqa: TC003
from typing import Annotated

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags
from semantic_version import Version as SemVer
from typer.core import TyperGroup

from dbrownell_ToolsDirectory import Lib


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):  # noqa: D101
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs) -> list[str]:  # noqa: ARG002, D102
        return list(self.commands.keys())  # pragma: no cover


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
class OutputType(str, Enum):
    """Specify the type of output to generate."""

    Bash = "bash"
    Batch = "batch"


# ----------------------------------------------------------------------
def _CreateHelp() -> str:
    return textwrap.dedent(
        r"""Create statements that add tools to the path.

        Tools should be organized by:

        |- <tool_directory>
           |- <tool_name>
              |- \[<version>]
                 |- \[<operating_system:{operating_systems}>]
                    |- \[<architecture:{architectures}>]
                       |- \[bin]

        Each of these examples are valid:

        |- Tools
           |- Tool1
           |- Tool2/bin
           |- Tool3/1.0.0
           |- Tool3/1.0.0/bin
           |- Tool4/v1.0.0
           |- Tool5/1.0.0/Linux
           |- Tool6/1.0.0/Linux/bin
           |- Tool7/1.0.0/Linux/x64
           |- Tool8/1.0.0/Linux/x64/bin

        """,
    ).format(
        operating_systems=" | ".join(Lib.OperatingSystemType.Linux.strings),
        architectures=" | ".join(Lib.ArchitectureType.x64.strings),
    )


# ----------------------------------------------------------------------
@app.command("EntryPoint", help=_CreateHelp(), no_args_is_help=True)
def EntryPoint(  # noqa: D103
    tool_directory: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, resolve_path=True, help="Path to the tool directory."),
    ],
    output_filename: Annotated[  # noqa: ARG001
        Path,
        typer.Argument(dir_okay=False, resolve_path=True, help="Path to the output file."),
    ],
    output_type: Annotated[  # noqa: ARG001
        OutputType,
        typer.Argument(help="The type of output to generate."),
    ],
    include: Annotated[
        list[str] | None,
        typer.Option(
            "--include", "-i", help="Name of tools to include; all tools found are included by default."
        ),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-e", help="Name of tools to exclude; no tools are excluded by default."),
    ] = None,
    tool_version: Annotated[
        list[str] | None,
        typer.Option(
            "--tool-version",
            "-tv",
            help="Specify the specific version of a tool to use; the latest version is used by default.",
        ),
    ] = None,
    no_generic_operating_system: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--no-generic-operating-system",
            "-ngos",
            help="Do not consider 'Generic' operating system versions when calculating the correct version.",
        ),
    ] = False,
    no_generic_architecture: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--no-generic-architecture",
            "-ngarch",
            help="Do not consider 'Generic' architecture versions when calculating the correct version.",
        ),
    ] = False,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        tool_infos = Lib.GetToolInfos(
            dm,
            tool_directory,
            set(include or []),
            set(exclude or []),
            _ExtractToolVersions(dm, tool_version or []),
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
            no_generic_operating_systems=no_generic_operating_system,
            no_generic_architectures=no_generic_architecture,
        )

        # TODO: Display purposes only
        for tool_info in tool_infos:
            dm.WriteInfo(str(tool_info))


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ExtractToolVersions(
    dm: DoneManager,
    args: list[str],
) -> dict[str, SemVer]:
    kvp_regex = re.compile(
        r"""
        ^                                   # Beginning of string
        (?P<tool_name>.+?)                  # Tool name
        \s*(?<!\\)\=\s*                     # Equal sign (not escaped)
        v?                                  # Optional 'v' prefix
        (?P<version>.+?)                    # Version
        $                                   # End of string
        """,
        re.VERBOSE,
    )

    results: dict[str, SemVer] = {}

    for arg in args:
        match = kvp_regex.match(arg)
        if not match:
            dm.WriteError(f"The tool version '{arg}' is not a valid command line argument.\n")
            continue

        tool_name = match.group("tool_name")
        version_str = match.group("version")

        try:
            version = SemVer.coerce(version_str)
        except ValueError:
            dm.WriteError(f"The version '{version_str}' for the tool '{tool_name}' is invalid.\n")
            continue

        results[tool_name] = version

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()  # pragma: no cover
