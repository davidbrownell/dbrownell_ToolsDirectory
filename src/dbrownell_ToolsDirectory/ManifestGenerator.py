# noqa: D100
from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING

import yaml

from dbrownell_Common.InflectEx import inflect

from dbrownell_ToolsDirectory.ToolInfo import (
    ArchitectureType,
    GenerateToolInfos,
    OperatingSystemType,
    ToolInfo,
)

if TYPE_CHECKING:
    from pathlib import Path

    from dbrownell_Common.Streams.DoneManager import DoneManager
    from semantic_version import Version as SemVer


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ToolConfiguration:
    """A specific configuration of a tool (version + OS + architecture combination)."""

    version: SemVer | None
    """Version of the tool, if a versioned directory was encountered."""

    operating_system: OperatingSystemType | Literal["Generic"] | None
    """Operating system of the tool, if an OS-specific directory was encountered."""

    architecture: ArchitectureType | Literal["Generic"] | None
    """Architecture of the tool, if an architecture-specific directory was encountered."""

    versioned_directory: Path
    """Root of a specific version of the tool, relative to tools_directory."""

    binary_directory: Path
    """Binary directory of a specific version of the tool, relative to tools_directory."""

    env_files: dict[Path, str] = field(default_factory=dict)
    """Environment files (relative to tools_directory) mapped to their contents."""


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ToolManifestEntry:
    """A tool with all its configurations."""

    name: str
    """Name of the tool."""

    configurations: list[ToolConfiguration] = field(default_factory=list)
    """All configurations (version + OS + architecture combinations), sorted by version in descending order."""


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ToolsManifest:
    """Complete manifest of all tools in a directory."""

    tools: list[ToolManifestEntry] = field(default_factory=list)
    """All tools in the directory."""


# ----------------------------------------------------------------------
# |
# |  Public Functions
# |
# ----------------------------------------------------------------------
def GenerateManifest(
    dm: DoneManager,
    tools_directory: Path,
    include_tools: set[str] | None = None,
    exclude_tools: set[str] | None = None,
) -> ToolsManifest:
    """Generate a manifest of all tools in a directory."""

    manifest_entries: list[ToolManifestEntry] = []

    with dm.Nested(
        f"Generating manifest for '{tools_directory}'...",
        lambda: "{} found".format(inflect.no("tool", len(manifest_entries))),
    ) as manifest_dm:
        include_tools = include_tools or set()
        exclude_tools = exclude_tools or set()

        # Collect ToolInfo objects by tool name
        tool_groups: dict[str, list[ToolInfo]] = {}

        for tool_directory in tools_directory.iterdir():
            if not tool_directory.is_dir():
                continue

            tool_name = tool_directory.name

            if tool_name in exclude_tools:
                manifest_dm.WriteVerbose(f"'{tool_name}' has been explicitly excluded.\n")
                continue

            if include_tools and tool_name not in include_tools:
                manifest_dm.WriteVerbose(f"'{tool_name}' has not been explicitly included.\n")
                continue

            # Generate all ToolInfo objects without filters
            tool_infos = list(
                GenerateToolInfos(
                    tool_directory,
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                ),
            )

            if not tool_infos:
                manifest_dm.WriteVerbose(f"No configurations found for '{tool_name}'.\n")
                continue

            tool_groups[tool_name] = tool_infos

        # Build the manifest
        for tool_name in sorted(tool_groups.keys()):
            tool_infos = tool_groups[tool_name]

            tool_configurations: list[ToolConfiguration] = []

            for tool_info in tool_infos:
                # Find existing env files (relative to tools_directory) and read their content
                existing_env_files: dict[Path, str] = {
                    env_file.relative_to(tools_directory): env_file.read_text(encoding="utf-8")
                    for env_file in tool_info.GeneratePotentialEnvFiles()
                    if env_file.is_file()
                }

                tool_configurations.append(
                    ToolConfiguration(
                        version=tool_info.version,
                        operating_system=tool_info.operating_system,
                        architecture=tool_info.architecture,
                        versioned_directory=tool_info.versioned_directory.relative_to(tools_directory),
                        binary_directory=tool_info.binary_directory.relative_to(tools_directory),
                        env_files=existing_env_files,
                    ),
                )

            manifest_entries.append(
                ToolManifestEntry(
                    name=tool_name,
                    configurations=tool_configurations,
                ),
            )

    return ToolsManifest(tools=manifest_entries)


# ----------------------------------------------------------------------
def WriteManifestYaml(
    manifest: ToolsManifest,
    output_path: Path,
) -> None:
    """Write a manifest to a YAML file."""

    yaml_data = _ManifestToDict(manifest)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data,
            f,
            Dumper=_LiteralBlockDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


# ----------------------------------------------------------------------
# |
# |  Private Types
# |
# ----------------------------------------------------------------------
class _LiteralBlockScalar(str):
    """A string subclass that will be serialized as a YAML literal block scalar (|)."""

    __slots__ = ()


# ----------------------------------------------------------------------
class _LiteralBlockDumper(yaml.SafeDumper):
    """Custom YAML dumper that represents _LiteralBlockScalar as literal block scalars."""


# ----------------------------------------------------------------------
# |
# |  Private Functions
# |
# ----------------------------------------------------------------------
def _LiteralBlockScalarRepresenter(
    dumper: yaml.SafeDumper,
    data: _LiteralBlockScalar,
) -> yaml.ScalarNode:
    """Represent a _LiteralBlockScalar as a literal block scalar."""

    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


_LiteralBlockDumper.add_representer(_LiteralBlockScalar, _LiteralBlockScalarRepresenter)


# ----------------------------------------------------------------------
def _ManifestToDict(manifest: ToolsManifest) -> dict:
    """Convert a ToolsManifest to a dictionary suitable for YAML serialization."""

    return {
        "tools": [_ToolManifestEntryToDict(entry) for entry in manifest.tools],
    }


# ----------------------------------------------------------------------
def _ToolManifestEntryToDict(entry: ToolManifestEntry) -> dict:
    """Convert a ToolManifestEntry to a dictionary."""

    return {
        "name": entry.name,
        "configurations": [_ToolConfigurationToDict(config) for config in entry.configurations],
    }


# ----------------------------------------------------------------------
def _ToolConfigurationToDict(config: ToolConfiguration) -> dict:
    """Convert a ToolConfiguration to a dictionary."""

    os_value: str | None

    if config.operating_system is None:
        os_value = None
    elif isinstance(config.operating_system, OperatingSystemType):
        os_value = config.operating_system.name
    elif isinstance(config.operating_system, str) and config.operating_system == "Generic":
        os_value = config.operating_system
    else:
        assert False, config.operating_system  # noqa: B011, PT015  # pragma: no cover

    arch_value: str | None

    if config.architecture is None:
        arch_value = None
    elif isinstance(config.architecture, ArchitectureType):
        arch_value = config.architecture.name
    elif isinstance(config.architecture, str) and config.architecture == "Generic":
        arch_value = config.architecture
    else:
        assert False, config.architecture  # noqa: B011, PT015  # pragma: no cover

    return {
        "version": str(config.version) if config.version is not None else None,
        "operating_system": os_value,
        "architecture": arch_value,
        "versioned_directory": str(config.versioned_directory.as_posix()),
        "binary_directory": str(config.binary_directory.as_posix()),
        "env_files": {
            str(path.as_posix()): _LiteralBlockScalar(content) for path, content in config.env_files.items()
        },
    }
