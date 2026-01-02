# noqa: D100
import platform
import sys

from dataclasses import dataclass
from enum import auto, Enum
from functools import cached_property
from typing import Literal, TYPE_CHECKING

from dbrownell_Common.InflectEx import inflect
from semantic_version import Version as SemVer

if TYPE_CHECKING:
    from collections.abc import Generator
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
    def string_map(self) -> dict[str, OperatingSystemType | Literal["Generic"]]:
        """Return strings that represent operating systems."""

        results: dict[str, OperatingSystemType | Literal["Generic"]] = {
            e.name: e for e in OperatingSystemType
        }

        results["Generic"] = "Generic"

        return results


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
    def string_map(self) -> dict[str, ArchitectureType | Literal["Generic"]]:
        """Return strings that represent architectures."""

        results: dict[str, ArchitectureType | Literal["Generic"]] = {e.name: e for e in ArchitectureType}

        results["Generic"] = "Generic"

        return results


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ToolInfo:
    """Information about a tool."""

    name: str
    """Name of the tool."""

    version: SemVer | None
    """Version of the tool, if a versioned directory was encountered."""

    operating_system: OperatingSystemType | Literal["Generic"] | None
    """Operating system of the tool, if an OS-specific directory was encountered."""

    architecture: ArchitectureType | Literal["Generic"] | None
    """Architecture of the tool, if an architecture-specific directory was encountered."""

    root_directory: Path
    """Root of the tool; all versioned directories are subdirectories of this."""

    versioned_directory: Path
    """Root of a specific version of the tool."""

    binary_directory: Path
    """Binary directory of a specific version of the tool."""

    # ----------------------------------------------------------------------
    def GeneratePotentialEnvFiles(self, file_extension: str = ".env") -> Generator[Path]:
        """Generate potential filenames for environment files, ordered from the least- to most-specific."""

        # ----------------------------------------------------------------------
        def ApplyStandardSuffixes(potential_suffixes: list[str]) -> None:
            assert not potential_suffixes
            potential_suffixes.append("")

        # ----------------------------------------------------------------------
        def ApplyVersionSuffixes(potential_suffixes: list[str]) -> None:
            if self.version is None:
                return

            potential_suffixes.append(f"-v{self.version}")

        # ----------------------------------------------------------------------
        def ApplyOperatingSystemSuffixes(potential_suffixes: list[str]) -> None:
            if self.operating_system is None:
                return

            suffix = (
                self.operating_system.name
                if isinstance(self.operating_system, OperatingSystemType)
                else self.operating_system
            )

            potential_suffixes.append(f"-{suffix}")
            potential_suffixes += [
                f"{potential_suffix}-{suffix}" for potential_suffix in potential_suffixes[1:-1]
            ]

        # ----------------------------------------------------------------------
        def ApplyArchitectureSuffixes(potential_suffixes: list[str]) -> None:
            if self.architecture is None:
                return

            suffix = (
                self.architecture.name
                if isinstance(self.architecture, ArchitectureType)
                else self.architecture
            )

            potential_suffixes.append(f"-{suffix}")
            potential_suffixes += [
                f"{potential_suffix}-{suffix}" for potential_suffix in potential_suffixes[1:-1]
            ]

        # ----------------------------------------------------------------------

        # Get a list of directories between the root and the versioned directory. Append "fake_file"
        # so that versioned_directory is included in the parents (without "fake_file", the implementation
        # thinks that versioned_directory is a file and not a directory).
        relative_paths = list(
            reversed((self.versioned_directory / "fake_file").relative_to(self.root_directory).parents)
        )

        # At most, there can be relative paths for:
        # 1) Root
        # 2) Version
        # 3) Operating System
        # 4) Architecture
        assert len(relative_paths) <= 4, relative_paths  # noqa: PLR2004

        # Root
        potential_suffixes: list[str] = []

        ApplyStandardSuffixes(potential_suffixes)
        ApplyVersionSuffixes(potential_suffixes)
        ApplyOperatingSystemSuffixes(potential_suffixes)
        ApplyArchitectureSuffixes(potential_suffixes)

        relative_path_offset = 0
        root = self.root_directory / relative_paths[relative_path_offset]

        yield from [root / f"{self.name}{suffix}{file_extension}" for suffix in potential_suffixes]

        # Version
        if self.version is not None:
            potential_suffixes = []

            ApplyStandardSuffixes(potential_suffixes)
            ApplyOperatingSystemSuffixes(potential_suffixes)
            ApplyArchitectureSuffixes(potential_suffixes)

            relative_path_offset += 1
            root = self.root_directory / relative_paths[relative_path_offset]

            yield from [root / f"{self.name}{suffix}{file_extension}" for suffix in potential_suffixes]

        # Operating System
        if self.operating_system is not None:
            potential_suffixes = []

            ApplyStandardSuffixes(potential_suffixes)
            ApplyArchitectureSuffixes(potential_suffixes)

            relative_path_offset += 1
            root = self.root_directory / relative_paths[relative_path_offset]

            yield from [root / f"{self.name}{suffix}{file_extension}" for suffix in potential_suffixes]

        # Architecture
        if self.architecture is not None:
            potential_suffixes = []

            ApplyStandardSuffixes(potential_suffixes)

            relative_path_offset += 1
            root = self.root_directory / relative_paths[relative_path_offset]

            yield root / f"{self.name}{file_extension}"


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

            tool_directory, semantic_version = _ApplyVersionDir(  #  noqa: PLW2901
                tool_dm,
                tool_name,
                tool_directory,
                tool_versions,
            )

            tool_directory, operating_system_type = _ApplyOperatingSystemDir(  # noqa: PLW2901
                tool_dm,
                tool_name,
                tool_directory,
                operating_system,
                no_generic_operating_systems=no_generic_operating_systems,
            )

            tool_directory, architecture_type = _ApplyArchitectureDir(  # noqa: PLW2901
                tool_dm,
                tool_name,
                tool_directory,
                architecture,
                no_generic_architectures=no_generic_architectures,
            )

            bin_tool_directory = _ApplyBinDir(tool_dm, tool_directory)

            if tool_dm.result != 0:
                continue

            results.append(
                ToolInfo(
                    tool_name,
                    semantic_version,
                    operating_system_type,
                    architecture_type,
                    root_directory,
                    tool_directory,
                    bin_tool_directory,
                ),
            )

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ApplyVersionDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    tool_versions: dict[str, SemVer],
) -> tuple[Path, SemVer | None]:
    working_version_dirs: list[tuple[SemVer, Path]] = []

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        try:
            version = SemVer.coerce(potential_dir.name.removeprefix("v"))
            working_version_dirs.append((version, potential_dir))
        except ValueError:
            continue

    if working_version_dirs:
        working_version_dirs.sort(key=lambda x: x[0], reverse=True)

        working_versions = dict(working_version_dirs)

        desired_version = tool_versions.get(
            tool_name,
            next(iter(working_versions)),
        )

        updated_working_dir = working_versions.get(desired_version)
        if updated_working_dir is not None:
            return updated_working_dir, desired_version

        dm.WriteError(
            f"No directory found for version '{desired_version}' for the tool '{tool_name}' in '{tool_directory}'.\n"
        )

    return tool_directory, None


# ----------------------------------------------------------------------
def _ApplyOperatingSystemDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    operating_system: OperatingSystemType,
    *,
    no_generic_operating_systems: bool,
) -> tuple[Path, OperatingSystemType | Literal["Generic"] | None]:
    operating_system_dirs: dict[str, tuple[Path, OperatingSystemType | Literal["Generic"]]] = {}

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        potential_mapped_info = operating_system.string_map.get(potential_dir.name)
        if potential_mapped_info is not None:
            operating_system_dirs[potential_dir.name] = (potential_dir, potential_mapped_info)

    if operating_system_dirs:
        if operating_system.name in operating_system_dirs:
            return operating_system_dirs[operating_system.name]

        if not no_generic_operating_systems and "Generic" in operating_system_dirs:
            return operating_system_dirs["Generic"]

        dm.WriteError(
            f"No directory found for '{operating_system.name}' for the tool '{tool_name}' in '{tool_directory}'.\n"
        )

    return tool_directory, None


# ----------------------------------------------------------------------
def _ApplyArchitectureDir(
    dm: DoneManager,
    tool_name: str,
    tool_directory: Path,
    architecture: ArchitectureType,
    *,
    no_generic_architectures: bool,
) -> tuple[Path, ArchitectureType | Literal["Generic"] | None]:
    architecture_dirs: dict[str, tuple[Path, ArchitectureType | Literal["Generic"]]] = {}

    for potential_dir in tool_directory.iterdir():
        if not potential_dir.is_dir():
            continue

        potential_mapped_info = architecture.string_map.get(potential_dir.name)
        if potential_mapped_info is not None:
            architecture_dirs[potential_dir.name] = (potential_dir, potential_mapped_info)

    if architecture_dirs:
        if architecture.name in architecture_dirs:
            return architecture_dirs[architecture.name]

        if not no_generic_architectures and "Generic" in architecture_dirs:
            return architecture_dirs["Generic"]

        dm.WriteError(
            f"No directory found for '{architecture.name}' for the tool '{tool_name}' in '{tool_directory}'.\n"
        )

    return tool_directory, None


# ----------------------------------------------------------------------
def _ApplyBinDir(
    dm: DoneManager,  # noqa: ARG001
    tool_directory: Path,
) -> Path:
    potential_dir = tool_directory / "bin"
    if potential_dir.is_dir():
        return potential_dir

    return tool_directory
