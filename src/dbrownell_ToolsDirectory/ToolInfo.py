# noqa: D100
import platform
import sys

from dataclasses import dataclass
from enum import auto, Enum
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
    @classmethod
    def StringMap(cls) -> dict[str, OperatingSystemType | Literal["Generic"]]:
        """Return strings that represent operating systems."""

        results: dict[str, OperatingSystemType | Literal["Generic"]] = {e.name: e for e in cls}

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
    @classmethod
    def StringMap(cls) -> dict[str, ArchitectureType | Literal["Generic"]]:
        """Return strings that represent architectures."""

        results: dict[str, ArchitectureType | Literal["Generic"]] = {e.name: e for e in cls}

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
def GetAllToolInfos(
    dm: DoneManager,
    tools_directory: Path,
    include_tools: set[str],
    exclude_tools: set[str],
    tool_versions: dict[str, SemVer],
    operating_system: OperatingSystemType,
    architecture: ArchitectureType,
    *,
    allow_generic_operating_systems: bool = True,
    allow_generic_architectures: bool = True,
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

            tool_name = tool_directory.name

            if tool_name in exclude_tools:
                tool_dm.WriteVerbose(f"'{tool_name}' has been explicitly excluded.\n")
                continue

            if include_tools and tool_name not in include_tools:
                tool_dm.WriteVerbose(f"'{tool_name}' has not been explicitly included.\n")
                continue

            try:
                tool_infos = list(
                    GenerateToolInfos(
                        tool_directory,
                        tool_versions.get(tool_name) or "latest",
                        operating_system,
                        architecture,
                        allow_generic_operating_system=allow_generic_operating_systems,
                        allow_generic_architecture=allow_generic_architectures,
                    ),
                )
            except ValueError as ex:
                tool_dm.WriteError(str(ex))
                continue

            if not tool_infos:
                tool_dm.WriteError(
                    f"No valid configurations found for the tool '{tool_name}' in '{tool_directory}'.\n"
                )
                continue

            assert len(tool_infos) == 1, tool_infos
            results.append(tool_infos[0])

    return results


# ----------------------------------------------------------------------
def GenerateToolInfos(
    tool_dir: Path,
    version_filter: SemVer | Literal["latest"] | None,
    operating_system_filter: OperatingSystemType | None,
    architecture_filter: ArchitectureType | None,
    *,
    allow_generic_operating_system: bool = True,
    allow_generic_architecture: bool = True,
) -> Generator[ToolInfo]:
    """Generate one or more ToolInfo objects for a specified tool directory."""

    tool_name = tool_dir.name

    for versioned_dir, version in _GenerateVersionedDirs(
        tool_name,
        tool_dir,
        version_filter,
    ):
        for operating_system_dir, operating_system in _GenerateOperatingSystemDirs(
            tool_name,
            versioned_dir,
            operating_system_filter,
            allow_generic_operating_system=allow_generic_operating_system,
        ):
            for architecture_dir, architecture in _GenerateArchitectureDirs(
                tool_name,
                operating_system_dir,
                architecture_filter,
                allow_generic_architecture=allow_generic_architecture,
            ):
                potential_bin_dir = architecture_dir / "bin"
                bin_dir = potential_bin_dir if potential_bin_dir.is_dir() else architecture_dir

                yield ToolInfo(
                    tool_name,
                    version,
                    operating_system,
                    architecture,
                    tool_dir,
                    architecture_dir,
                    bin_dir,
                )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GenerateVersionedDirs(
    tool_name: str,
    working_dir: Path,
    dir_filter: SemVer | Literal["latest"] | None,
) -> Generator[tuple[Path, SemVer | None]]:
    versioned_infos: list[tuple[SemVer, Path]] = []

    for potential_dir in working_dir.iterdir():
        if not potential_dir.is_dir():
            continue

        try:
            version = SemVer.coerce(potential_dir.name.removeprefix("v"))
            versioned_infos.append((version, potential_dir))
        except ValueError:
            # This is an indication that the directory is not a version directory
            continue

    if not versioned_infos:
        yield working_dir, None
        return

    versioned_infos.sort(key=lambda x: x[0], reverse=True)

    if dir_filter is not None:
        versioned_infos_dict = dict(versioned_infos)

        if isinstance(dir_filter, SemVer):
            desired_version = dir_filter
        elif isinstance(dir_filter, str) and dir_filter == "latest":
            desired_version = next(iter(versioned_infos_dict))
        else:
            assert False, dir_filter  # noqa: B011, PT015  # pragma: no cover

        updated_working_dir = versioned_infos_dict.get(desired_version)
        if updated_working_dir is None:
            msg = f"No directory found for version '{desired_version}' for the tool '{tool_name}' in '{working_dir}'."
            raise ValueError(msg)

        yield updated_working_dir, desired_version

    else:
        for versioned_info in versioned_infos:
            yield versioned_info[1], versioned_info[0]


# ----------------------------------------------------------------------
def _GenerateOperatingSystemDirs(
    tool_name: str,
    working_dir: Path,
    dir_filter: OperatingSystemType | None,
    *,
    allow_generic_operating_system: bool,
) -> Generator[tuple[Path, OperatingSystemType | Literal["Generic"] | None]]:
    os_string_map = OperatingSystemType.StringMap()
    os_infos: dict[str, tuple[Path, OperatingSystemType | Literal["Generic"]]] = {}

    for potential_dir in working_dir.iterdir():
        if not potential_dir.is_dir():
            continue

        potential_mapped_type = os_string_map.get(potential_dir.name)
        if potential_mapped_type is not None:
            os_infos[potential_dir.name] = (potential_dir, potential_mapped_type)

    if not os_infos:
        yield working_dir, None
        return

    if dir_filter is not None:
        os_info = os_infos.get(dir_filter.name)

        if os_info is None:
            if allow_generic_operating_system:
                os_info = os_infos.get("Generic")

            if os_info is None:
                msg = f"No directory found for '{dir_filter.name}' for the tool '{tool_name}' in '{working_dir}'."
                raise ValueError(msg)

        yield os_info

    else:
        yield from os_infos.values()


# ----------------------------------------------------------------------
def _GenerateArchitectureDirs(
    tool_name: str,
    working_dir: Path,
    dir_filter: ArchitectureType | None,
    *,
    allow_generic_architecture: bool,
) -> Generator[tuple[Path, ArchitectureType | Literal["Generic"] | None]]:
    arch_string_map = ArchitectureType.StringMap()
    arch_infos: dict[str, tuple[Path, ArchitectureType | Literal["Generic"]]] = {}

    for potential_dir in working_dir.iterdir():
        if not potential_dir.is_dir():
            continue

        potential_mapped_type = arch_string_map.get(potential_dir.name)
        if potential_mapped_type is not None:
            arch_infos[potential_dir.name] = (potential_dir, potential_mapped_type)

    if not arch_infos:
        yield working_dir, None
        return

    if dir_filter is not None:
        arch_info = arch_infos.get(dir_filter.name)

        if arch_info is None:
            if allow_generic_architecture:
                arch_info = arch_infos.get("Generic")

            if arch_info is None:
                msg = f"No directory found for '{dir_filter.name}' for the tool '{tool_name}' in '{working_dir}'."
                raise ValueError(msg)

        yield arch_info

    else:
        yield from arch_infos.values()
