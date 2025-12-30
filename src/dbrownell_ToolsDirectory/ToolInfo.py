# noqa: D100
import platform
import sys

from dataclasses import dataclass
from enum import auto, Enum
from functools import cached_property
from typing import TYPE_CHECKING

from dbrownell_Common.InflectEx import inflect
from semantic_version import Version as SemVer

if TYPE_CHECKING:
    from pathlib import Path

    from dbrownell_Common.Streams.DoneManager import DoneManager


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class OperatingSystemType(Enum):
    """Specify the operating system."""

    Linux = auto()
    MacOS = auto()
    Windows = auto()

    # ----------------------------------------------------------------------
    @classmethod
    def Calculate(cls) -> OperatingSystemType:
        """Calculate the current operating system."""

        platform_str = sys.platform.lower()

        if platform_str.startswith("linux"):
            return OperatingSystemType.Linux

        if platform_str.startswith("darwin"):
            return OperatingSystemType.MacOS

        if platform_str.startswith("win32"):
            return OperatingSystemType.Windows

        msg = f"Unsupported platform: '{platform_str}'"
        raise Exception(msg)

    # ----------------------------------------------------------------------
    @cached_property
    def strings(self) -> set[str]:
        """Return strings that represent operating systems."""

        results: list[str] = [e.name for e in OperatingSystemType]

        results.append("Generic")

        return set(results)


# ----------------------------------------------------------------------
class ArchitectureType(Enum):
    """Specify the system architecture."""

    x64 = auto()
    x86 = auto()
    ARM64 = auto()
    ARM = auto()

    # ----------------------------------------------------------------------
    @classmethod
    def Calculate(cls) -> ArchitectureType:
        """Calculate the current system architecture."""

        arch = platform.machine().lower()

        if arch == "arm64":
            return ArchitectureType.ARM64
        if arch == "amd":
            return ArchitectureType.ARM

        if arch not in ["x86_64", "amd64"]:
            msg = f"Unsupported architecture: '{arch}'"
            raise Exception(msg)

        return ArchitectureType.x64 if sys.maxsize > 2**32 else ArchitectureType.x86

    # ----------------------------------------------------------------------
    @cached_property
    def strings(self) -> set[str]:
        """Return strings that represent architectures."""

        results: list[str] = [e.name for e in ArchitectureType]

        results.append("Generic")

        return set(results)


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ToolInfo:
    """Information about a tool."""

    name: str
    """Name of the tool."""

    root_directory: Path
    """Root of the tool; all versioned directories are subdirectories of this."""

    versioned_directory: Path
    """Root of a specific version of the tool."""

    binary_directory: Path
    """Binary directory of a specific version of the tool."""


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def GetToolInfos(
    dm: DoneManager,
    tools_directory: Path,
    include_tools: set[str],
    exclude_tools: set[str],
    tool_versions: dict[str, SemVer],
    operating_system: OperatingSystemType,
    architecture: ArchitectureType,
    *,
    no_generic_operating_systems: bool = False,
    no_generic_architectures: bool = False,
) -> list[ToolInfo]:
    """Return information about tools in a specified directory."""

    results: list[ToolInfo] = []

    with dm.Nested(
        f"Parsing tools in '{tools_directory}'...",
        lambda: "{} found".format(inflect.no("tool", len(results))),
        suffix="\n",
    ) as tool_dm:
        for tool_directory in tools_directory.iterdir():
            if not tool_directory.is_dir():
                continue

            root_directory = tool_directory
            tool_name = tool_directory.name

            if tool_name in exclude_tools:
                tool_dm.WriteVerbose(f"'{tool_name}' has been explicitly excluded.\n")
                continue

            if include_tools and tool_name not in include_tools:
                tool_dm.WriteVerbose(f"'{tool_name}' has not been explicitly included.\n")
                continue

            tool_directory = _ApplyVersionDir(tool_dm, tool_name, tool_directory, tool_versions)  # noqa: PLW2901

            tool_directory = _ApplyOperatingSystemDir(  # noqa: PLW2901
                tool_dm,
                tool_name,
                tool_directory,
                operating_system,
                no_generic_operating_systems=no_generic_operating_systems,
            )

            tool_directory = _ApplyArchitectureDir(  # noqa: PLW2901
                tool_dm,
                tool_name,
                tool_directory,
                architecture,
                no_generic_architectures=no_generic_architectures,
            )

            bin_tool_directory = _ApplyBinDir(tool_dm, tool_directory)

            if tool_dm.result != 0:
                continue

            results.append(ToolInfo(tool_name, root_directory, tool_directory, bin_tool_directory))

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ApplyVersionDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    tool_versions: dict[str, SemVer],
) -> Path:
    working_version_dirs: list[tuple[SemVer, Path]] = []

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        try:
            version = SemVer.coerce(potential_dir.name.removeprefix("v"))
            working_version_dirs.append((version, potential_dir))
        except ValueError:
            continue

    if not working_version_dirs:
        return tool_directory

    working_version_dirs.sort(key=lambda x: x[0], reverse=True)

    working_versions = dict(working_version_dirs)

    desired_version = tool_versions.get(
        tool_name,
        next(iter(working_versions)),
    )

    updated_working_dir = working_versions.get(desired_version)
    if updated_working_dir is not None:
        return updated_working_dir

    dm.WriteError(
        f"No directory found for version '{desired_version}' for the tool '{tool_name}' in '{tool_directory}'.\n"
    )

    return tool_directory


# ----------------------------------------------------------------------
def _ApplyOperatingSystemDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    operating_system: OperatingSystemType,
    *,
    no_generic_operating_systems: bool,
) -> Path:
    operating_system_dirs: dict[str, Path] = {}

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        if potential_dir.name in operating_system.strings:
            operating_system_dirs[potential_dir.name] = potential_dir

    if not operating_system_dirs:
        return tool_directory

    if operating_system.name in operating_system_dirs:
        return operating_system_dirs[operating_system.name]

    if not no_generic_operating_systems and "Generic" in operating_system_dirs:
        return operating_system_dirs["Generic"]

    dm.WriteError(
        f"No directory found for '{operating_system.name}' for the tool '{tool_name}' in '{tool_directory}'.\n"
    )
    return tool_directory


# ----------------------------------------------------------------------
def _ApplyArchitectureDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    architecture: ArchitectureType,
    *,
    no_generic_architectures: bool,
) -> Path:
    architecture_dirs: dict[str, Path] = {}

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        if potential_dir.name in architecture.strings:
            architecture_dirs[potential_dir.name] = potential_dir

    if not architecture_dirs:
        return tool_directory

    if architecture.name in architecture_dirs:
        return architecture_dirs[architecture.name]

    if not no_generic_architectures and "Generic" in architecture_dirs:
        return architecture_dirs["Generic"]

    dm.WriteError(
        f"No directory found for '{architecture.name}' for the tool '{tool_name}' in '{tool_directory}'.\n"
    )
    return tool_directory


# ----------------------------------------------------------------------
def _ApplyBinDir(
    dm: DoneManager,  # noqa: ARG001
    tool_directory: Path,
) -> Path:
    potential_dir = tool_directory / "bin"
    if potential_dir.is_dir():
        return potential_dir

    return tool_directory
