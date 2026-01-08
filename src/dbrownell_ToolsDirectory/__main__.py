# noqa: D100
import re
import sys
import textwrap

from enum import Enum
from pathlib import Path
from typing import Annotated, TYPE_CHECKING

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags
from semantic_version import Version as SemVer
from typer.core import TyperGroup

from dbrownell_ToolsDirectory import __version__
from dbrownell_ToolsDirectory.CreateShellCommands import CreateShellCommands
from dbrownell_ToolsDirectory.Shell.BashCommandVisitor import BashCommandVisitor
from dbrownell_ToolsDirectory.Shell.BatchCommandVisitor import BatchCommandVisitor
from dbrownell_ToolsDirectory.Shell.PowerShellCommandVisitor import PowerShellCommandVisitor
from dbrownell_ToolsDirectory import ToolInfo

if TYPE_CHECKING:
    from dbrownell_ToolsDirectory.Shell.Commands import Command


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
    PowerShell = "powershell"


# ----------------------------------------------------------------------
def _CreateHelp() -> str:
    return textwrap.dedent(
        r"""Create statements that add tools to the path.

        Tools should be organized by:

        ├── <tool_directory>/
            └── <tool_name>/
                └── \[<version>/]
                    └── \[<operating_system:{operating_systems}>/]
                        └── \[<architecture:{architectures}>/]
                            └── \[bin/]

        Each of these examples are supported:

        Tools/
        ├── Tool1/
        ├── Tool2/
        │   └── bin/
        ├── Tool3/
        │   └── 1.0.0/
        │       └── bin/
        ├── Tool4/
        │   └── v1.0.0/
        ├── Tool5/
        │   └── 1.0.0/
        │       └── Linux/
        ├── Tool6/
        │   └── 1.0.0/
        │       └── Linux/
        │           └── bin/
        ├── Tool7/
        │   └── 1.0.0/
        │       └── Linux/
        │           └── x64/
        └── Tool8/
            └── 1.0.0/
                └── Linux/
                    └── x64/
                        └── bin/

        """,
    ).format(
        operating_systems=" | ".join(ToolInfo.OperatingSystemType.Linux.string_map.keys()),
        architectures=" | ".join(ToolInfo.ArchitectureType.x64.string_map.keys()),
    )


# ----------------------------------------------------------------------
@app.command("activate", help=_CreateHelp(), no_args_is_help=True)
def Activate(  # noqa: D103
    output_filename: Annotated[
        Path,
        typer.Argument(dir_okay=False, resolve_path=True, path_type=Path, help="Path to the output file."),  # ty: ignore[no-matching-overload]
    ],
    output_type: Annotated[
        OutputType,
        typer.Argument(help="The type of output to generate."),
    ],
    tool_directory: Annotated[
        Path,
        typer.Argument(  # ty: ignore[no-matching-overload]
            exists=True,
            file_okay=False,
            resolve_path=True,
            path_type=Path,
            help="Path to the tool directory.",
        ),
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
        if output_filename.is_file():
            output_filename.unlink()

        # Get the tools
        tool_infos = ToolInfo.GetToolInfos(
            dm,
            tool_directory,
            set(include or []),
            set(exclude or []),
            _ExtractToolVersions(dm, tool_version or []),
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
            no_generic_operating_systems=no_generic_operating_system,
            no_generic_architectures=no_generic_architecture,
        )

        if not tool_infos:
            dm.WriteError(f"No tools were found in '{tool_directory}'.\n")
            return

        # Display the tools
        if dm.is_verbose:
            for tool_info in tool_infos:
                header = tool_info.name

                if tool_info.version is not None:
                    header += f" (v{tool_info.version})"

                dm.WriteLine(
                    textwrap.dedent(
                        """\
                        {header}
                        {sep}
                        Root:              {root}
                        Versioned:         {versioned}
                        Binary:            {binary}
                        Operating System:  {os}
                        Architecture:      {arch}

                        """,
                    ).format(
                        header=header,
                        sep="-" * max(len(header), 17),
                        root=tool_info.root_directory,
                        versioned=tool_info.versioned_directory,
                        binary=tool_info.binary_directory,
                        os=tool_info.operating_system.name
                        if isinstance(tool_info.operating_system, ToolInfo.OperatingSystemType)
                        else tool_info.operating_system,
                        arch=tool_info.architecture.name
                        if isinstance(tool_info.architecture, ToolInfo.ArchitectureType)
                        else tool_info.architecture,
                    ),
                )

        # Create the shell statements
        commands: list[Command] = CreateShellCommands(dm, tool_infos)

        # Write the output
        if output_type == OutputType.Bash:
            command_visitor = BashCommandVisitor()
        elif output_type == OutputType.Batch:
            command_visitor = BatchCommandVisitor()
        elif output_type == OutputType.PowerShell:
            command_visitor = PowerShellCommandVisitor()
        else:
            assert False, output_type  # noqa: B011, PT015  # pragma: no cover

        output_filename.parent.mkdir(parents=True, exist_ok=True)
        with output_filename.open("w", encoding="utf-8") as f:
            for command in commands:
                result = command_visitor.Accept(command)

                if isinstance(result, str):
                    f.write(result)


# ----------------------------------------------------------------------
@app.command("version", no_args_is_help=False)
def Version() -> None:
    """Display the version of this tool."""
    sys.stdout.write(f"{__version__}\n")


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
