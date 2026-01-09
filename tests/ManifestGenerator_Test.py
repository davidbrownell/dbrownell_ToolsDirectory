# noqa: D100
from pathlib import Path

import yaml

from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from pyfakefs.fake_filesystem import FakeFilesystem
from semantic_version import Version as SemVer

from dbrownell_ToolsDirectory.ManifestGenerator import (
    GenerateManifest,
    ToolConfiguration,
    ToolManifestEntry,
    ToolsManifest,
    WriteManifestYaml,
)
from dbrownell_ToolsDirectory.ToolInfo import ArchitectureType, OperatingSystemType


# ----------------------------------------------------------------------
def _GenerateManifest(
    tools_directory: Path,
    include_tools: set[str] | None = None,
    exclude_tools: set[str] | None = None,
) -> ToolsManifest:
    """Helper function to generate manifest with a DoneManager."""
    dm_and_sink = iter(GenerateDoneManagerAndContent())

    return GenerateManifest(
        next(dm_and_sink),
        tools_directory,
        include_tools=include_tools,
        exclude_tools=exclude_tools,
    )


# ----------------------------------------------------------------------
class TestToolConfiguration:
    """Tests for ToolConfiguration dataclass."""

    # ----------------------------------------------------------------------
    def test_DefaultEnvFiles(self) -> None:
        config = ToolConfiguration(
            version=SemVer("1.0.0"),
            operating_system=OperatingSystemType.Linux,
            architecture=ArchitectureType.x64,
            versioned_directory=Path("Tool1/1.0.0/Linux/x64"),
            binary_directory=Path("Tool1/1.0.0/Linux/x64/bin"),
        )

        assert config.env_files == []

    # ----------------------------------------------------------------------
    def test_WithEnvFiles(self) -> None:
        config = ToolConfiguration(
            version=SemVer("1.0.0"),
            operating_system=OperatingSystemType.Linux,
            architecture=ArchitectureType.x64,
            versioned_directory=Path("Tool1/1.0.0/Linux/x64"),
            binary_directory=Path("Tool1/1.0.0/Linux/x64/bin"),
            env_files=[Path("Tool1/Tool1.env")],
        )

        assert config.env_files == [Path("Tool1/Tool1.env")]


# ----------------------------------------------------------------------
class TestToolManifestEntry:
    """Tests for ToolManifestEntry dataclass."""

    # ----------------------------------------------------------------------
    def test_DefaultConfigurations(self) -> None:
        entry = ToolManifestEntry(
            name="Tool1",
        )

        assert entry.configurations == []


# ----------------------------------------------------------------------
class TestToolsManifest:
    """Tests for ToolsManifest dataclass."""

    # ----------------------------------------------------------------------
    def test_DefaultTools(self) -> None:
        manifest = ToolsManifest()

        assert manifest.tools == []


# ----------------------------------------------------------------------
class TestGenerateManifest:
    """Tests for GenerateManifest function."""

    # ----------------------------------------------------------------------
    def test_EmptyDirectory(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir)

        manifest = _GenerateManifest(tools_dir)

        assert manifest.tools == []

    # ----------------------------------------------------------------------
    def test_SingleToolNoVersionNoOsNoArch(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert manifest.tools[0].name == "Tool1"
        assert len(manifest.tools[0].configurations) == 1
        config = manifest.tools[0].configurations[0]
        assert config.version is None
        assert config.operating_system is None
        assert config.architecture is None
        assert config.versioned_directory == Path("Tool1")
        assert config.binary_directory == Path("Tool1")
        assert config.env_files == []

    # ----------------------------------------------------------------------
    def test_SingleToolWithBinDirectory(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "bin")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        config = manifest.tools[0].configurations[0]
        assert config.versioned_directory == Path("Tool1")
        assert config.binary_directory == Path("Tool1/bin")

    # ----------------------------------------------------------------------
    def test_SingleToolWithVersion(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "1.0.0")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert len(manifest.tools[0].configurations) == 1
        config = manifest.tools[0].configurations[0]
        assert config.version == SemVer("1.0.0")
        assert config.versioned_directory == Path("Tool1/1.0.0")
        assert config.binary_directory == Path("Tool1/1.0.0")

    # ----------------------------------------------------------------------
    def test_SingleToolWithMultipleVersions(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "1.0.0")
        fs.create_dir(tools_dir / "Tool1" / "1.5.0")
        fs.create_dir(tools_dir / "Tool1" / "2.0.0")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert len(manifest.tools[0].configurations) == 3

        config0 = manifest.tools[0].configurations[0]
        assert config0.version == SemVer("2.0.0")
        assert config0.operating_system is None
        assert config0.architecture is None
        assert config0.versioned_directory == Path("Tool1/2.0.0")
        assert config0.binary_directory == Path("Tool1/2.0.0")
        assert config0.env_files == []

        config1 = manifest.tools[0].configurations[1]
        assert config1.version == SemVer("1.5.0")
        assert config1.operating_system is None
        assert config1.architecture is None
        assert config1.versioned_directory == Path("Tool1/1.5.0")
        assert config1.binary_directory == Path("Tool1/1.5.0")
        assert config1.env_files == []

        config2 = manifest.tools[0].configurations[2]
        assert config2.version == SemVer("1.0.0")
        assert config2.operating_system is None
        assert config2.architecture is None
        assert config2.versioned_directory == Path("Tool1/1.0.0")
        assert config2.binary_directory == Path("Tool1/1.0.0")
        assert config2.env_files == []

    # ----------------------------------------------------------------------
    def test_SingleToolWithOS(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "Linux")
        fs.create_dir(tools_dir / "Tool1" / "Windows")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert len(manifest.tools[0].configurations) == 2

        config0 = manifest.tools[0].configurations[0]
        assert config0.version is None
        assert config0.operating_system == OperatingSystemType.Linux
        assert config0.architecture is None
        assert config0.versioned_directory == Path("Tool1/Linux")
        assert config0.binary_directory == Path("Tool1/Linux")
        assert config0.env_files == []

        config1 = manifest.tools[0].configurations[1]
        assert config1.version is None
        assert config1.operating_system == OperatingSystemType.Windows
        assert config1.architecture is None
        assert config1.versioned_directory == Path("Tool1/Windows")
        assert config1.binary_directory == Path("Tool1/Windows")
        assert config1.env_files == []

    # ----------------------------------------------------------------------
    def test_SingleToolWithOSAndArch(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "Linux" / "ARM64")
        fs.create_dir(tools_dir / "Tool1" / "Linux" / "x64")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert len(manifest.tools[0].configurations) == 2

        config0 = manifest.tools[0].configurations[0]
        assert config0.version is None
        assert config0.operating_system == OperatingSystemType.Linux
        assert config0.architecture == ArchitectureType.ARM64
        assert config0.versioned_directory == Path("Tool1/Linux/ARM64")
        assert config0.binary_directory == Path("Tool1/Linux/ARM64")
        assert config0.env_files == []

        config1 = manifest.tools[0].configurations[1]
        assert config1.version is None
        assert config1.operating_system == OperatingSystemType.Linux
        assert config1.architecture == ArchitectureType.x64
        assert config1.versioned_directory == Path("Tool1/Linux/x64")
        assert config1.binary_directory == Path("Tool1/Linux/x64")
        assert config1.env_files == []

    # ----------------------------------------------------------------------
    def test_SingleToolWithVersionOsArch(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "1.0.0" / "Linux" / "x64" / "bin")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert manifest.tools[0].configurations[0].version == SemVer("1.0.0")
        config = manifest.tools[0].configurations[0]
        assert config.operating_system == OperatingSystemType.Linux
        assert config.architecture == ArchitectureType.x64
        assert config.versioned_directory == Path("Tool1/1.0.0/Linux/x64")
        assert config.binary_directory == Path("Tool1/1.0.0/Linux/x64/bin")

    # ----------------------------------------------------------------------
    def test_SingleToolWithGenericOS(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "Generic")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        config = manifest.tools[0].configurations[0]
        assert config.operating_system == "Generic"
        assert config.versioned_directory == Path("Tool1/Generic")
        assert config.binary_directory == Path("Tool1/Generic")

    # ----------------------------------------------------------------------
    def test_SingleToolWithGenericArch(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "Linux" / "Generic")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        config = manifest.tools[0].configurations[0]
        assert config.operating_system == OperatingSystemType.Linux
        assert config.architecture == "Generic"
        assert config.versioned_directory == Path("Tool1/Linux/Generic")
        assert config.binary_directory == Path("Tool1/Linux/Generic")

    # ----------------------------------------------------------------------
    def test_MultipleTools(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "ToolA")
        fs.create_dir(tools_dir / "ToolB")
        fs.create_dir(tools_dir / "ToolC")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 3
        # Tools should be sorted alphabetically
        assert manifest.tools[0].name == "ToolA"
        assert manifest.tools[0].configurations[0].versioned_directory == Path("ToolA")
        assert manifest.tools[0].configurations[0].binary_directory == Path("ToolA")
        assert manifest.tools[1].name == "ToolB"
        assert manifest.tools[1].configurations[0].versioned_directory == Path("ToolB")
        assert manifest.tools[1].configurations[0].binary_directory == Path("ToolB")
        assert manifest.tools[2].name == "ToolC"
        assert manifest.tools[2].configurations[0].versioned_directory == Path("ToolC")
        assert manifest.tools[2].configurations[0].binary_directory == Path("ToolC")

    # ----------------------------------------------------------------------
    def test_IncludeTools(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "ToolA")
        fs.create_dir(tools_dir / "ToolB")
        fs.create_dir(tools_dir / "ToolC")

        manifest = _GenerateManifest(tools_dir, include_tools={"ToolA", "ToolC"})

        assert len(manifest.tools) == 2
        assert manifest.tools[0].name == "ToolA"
        assert manifest.tools[0].configurations[0].versioned_directory == Path("ToolA")
        assert manifest.tools[0].configurations[0].binary_directory == Path("ToolA")
        assert manifest.tools[1].name == "ToolC"
        assert manifest.tools[1].configurations[0].versioned_directory == Path("ToolC")
        assert manifest.tools[1].configurations[0].binary_directory == Path("ToolC")

    # ----------------------------------------------------------------------
    def test_ExcludeTools(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "ToolA")
        fs.create_dir(tools_dir / "ToolB")
        fs.create_dir(tools_dir / "ToolC")

        manifest = _GenerateManifest(tools_dir, exclude_tools={"ToolB"})

        assert len(manifest.tools) == 2
        assert manifest.tools[0].name == "ToolA"
        assert manifest.tools[0].configurations[0].versioned_directory == Path("ToolA")
        assert manifest.tools[0].configurations[0].binary_directory == Path("ToolA")
        assert manifest.tools[1].name == "ToolC"
        assert manifest.tools[1].configurations[0].versioned_directory == Path("ToolC")
        assert manifest.tools[1].configurations[0].binary_directory == Path("ToolC")

    # ----------------------------------------------------------------------
    def test_IncludeAndExcludeTools(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "ToolA")
        fs.create_dir(tools_dir / "ToolB")
        fs.create_dir(tools_dir / "ToolC")

        manifest = _GenerateManifest(
            tools_dir,
            include_tools={"ToolA", "ToolB"},
            exclude_tools={"ToolB"},
        )

        assert len(manifest.tools) == 1
        assert manifest.tools[0].name == "ToolA"
        assert manifest.tools[0].configurations[0].versioned_directory == Path("ToolA")
        assert manifest.tools[0].configurations[0].binary_directory == Path("ToolA")

    # ----------------------------------------------------------------------
    def test_WithExistingEnvFile(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1")
        fs.create_file(tools_dir / "Tool1" / "Tool1.env")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        config = manifest.tools[0].configurations[0]
        assert config.versioned_directory == Path("Tool1")
        assert config.binary_directory == Path("Tool1")
        assert config.env_files == [Path("Tool1/Tool1.env")]

    # ----------------------------------------------------------------------
    def test_WithMultipleExistingEnvFiles(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1" / "1.0.0" / "Linux")
        fs.create_file(tools_dir / "Tool1" / "Tool1.env")
        fs.create_file(tools_dir / "Tool1" / "1.0.0" / "Tool1-Linux.env")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        config = manifest.tools[0].configurations[0]
        assert config.versioned_directory == Path("Tool1/1.0.0/Linux")
        assert config.binary_directory == Path("Tool1/1.0.0/Linux")
        assert len(config.env_files) == 2
        assert Path("Tool1/Tool1.env") in config.env_files
        assert Path("Tool1/1.0.0/Tool1-Linux.env") in config.env_files

    # ----------------------------------------------------------------------
    def test_IgnoresNonDirectories(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_dir(tools_dir / "Tool1")
        fs.create_file(tools_dir / "README.md")

        manifest = _GenerateManifest(tools_dir)

        assert len(manifest.tools) == 1
        assert manifest.tools[0].name == "Tool1"
        assert manifest.tools[0].configurations[0].versioned_directory == Path("Tool1")
        assert manifest.tools[0].configurations[0].binary_directory == Path("Tool1")

    # ----------------------------------------------------------------------
    def test_NoToolsInDirectory(self, fs: FakeFilesystem) -> None:
        tools_dir = Path("/tools")
        fs.create_file(tools_dir / "README.md")
        fs.create_file(tools_dir / "config.yaml")

        manifest = _GenerateManifest(tools_dir)

        assert manifest.tools == []


# ----------------------------------------------------------------------
class TestWriteManifestYaml:
    """Tests for WriteManifestYaml function."""

    # ----------------------------------------------------------------------
    def test_EmptyManifest(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest()

        WriteManifestYaml(manifest, output_path)

        assert output_path.exists()
        with output_path.open() as f:
            data = yaml.safe_load(f)
        assert data == {"tools": []}

    # ----------------------------------------------------------------------
    def test_CreatesParentDirectories(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/subdir/manifest.yaml")
        manifest = ToolsManifest()

        WriteManifestYaml(manifest, output_path)

        assert output_path.exists()

    # ----------------------------------------------------------------------
    def test_SimpleManifest(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=None,
                            operating_system=None,
                            architecture=None,
                            versioned_directory=Path("Tool1"),
                            binary_directory=Path("Tool1"),
                            env_files=[],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            data = yaml.safe_load(f)

        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "Tool1"
        assert data["tools"][0]["configurations"][0]["version"] is None
        assert data["tools"][0]["configurations"][0]["operating_system"] is None
        assert data["tools"][0]["configurations"][0]["architecture"] is None

    # ----------------------------------------------------------------------
    def test_ManifestWithVersion(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=SemVer("1.0.0"),
                            operating_system=None,
                            architecture=None,
                            versioned_directory=Path("Tool1/1.0.0"),
                            binary_directory=Path("Tool1/1.0.0"),
                            env_files=[],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            data = yaml.safe_load(f)

        assert data["tools"][0]["configurations"][0]["version"] == "1.0.0"

    # ----------------------------------------------------------------------
    def test_ManifestWithOsAndArch(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=None,
                            operating_system=OperatingSystemType.Linux,
                            architecture=ArchitectureType.x64,
                            versioned_directory=Path("Tool1/Linux/x64"),
                            binary_directory=Path("Tool1/Linux/x64"),
                            env_files=[],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            data = yaml.safe_load(f)

        config = data["tools"][0]["configurations"][0]
        assert config["operating_system"] == "Linux"
        assert config["architecture"] == "x64"

    # ----------------------------------------------------------------------
    def test_ManifestWithGenericOs(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=None,
                            operating_system="Generic",
                            architecture=None,
                            versioned_directory=Path("Tool1/Generic"),
                            binary_directory=Path("Tool1/Generic"),
                            env_files=[],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            data = yaml.safe_load(f)

        config = data["tools"][0]["configurations"][0]
        assert config["operating_system"] == "Generic"

    # ----------------------------------------------------------------------
    def test_ManifestWithEnvFiles(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=None,
                            operating_system=None,
                            architecture=None,
                            versioned_directory=Path("Tool1"),
                            binary_directory=Path("Tool1"),
                            env_files=[
                                Path("Tool1/Tool1.env"),
                                Path("Tool1/Tool1-Linux.env"),
                            ],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            data = yaml.safe_load(f)

        config = data["tools"][0]["configurations"][0]
        assert config["env_files"] == ["Tool1/Tool1.env", "Tool1/Tool1-Linux.env"]

    # ----------------------------------------------------------------------
    def test_UsesForwardSlashesInPaths(self, fs: FakeFilesystem) -> None:
        output_path = Path("/output/manifest.yaml")
        manifest = ToolsManifest(
            tools=[
                ToolManifestEntry(
                    name="Tool1",
                    configurations=[
                        ToolConfiguration(
                            version=SemVer("1.0.0"),
                            operating_system=OperatingSystemType.Linux,
                            architecture=ArchitectureType.x64,
                            versioned_directory=Path("Tool1/1.0.0/Linux/x64"),
                            binary_directory=Path("Tool1/1.0.0/Linux/x64/bin"),
                            env_files=[Path("Tool1/Tool1.env")],
                        ),
                    ],
                ),
            ],
        )

        WriteManifestYaml(manifest, output_path)

        with output_path.open() as f:
            content = f.read()

        # Check that paths use forward slashes
        assert "Tool1/1.0.0/Linux/x64" in content
        assert "Tool1/1.0.0/Linux/x64/bin" in content


# ----------------------------------------------------------------------
class TestIntegration:
    """Integration tests for manifest generation."""

    # ----------------------------------------------------------------------
    def test_FullWorkflow(self, fs: FakeFilesystem) -> None:
        # Create a complex tool directory structure
        tools_dir = Path("/tools")

        # Tool1 with versions, OS, and arch
        fs.create_dir(tools_dir / "Tool1" / "1.0.0" / "Linux" / "x64" / "bin")
        fs.create_dir(tools_dir / "Tool1" / "1.0.0" / "Windows" / "x64")
        fs.create_dir(tools_dir / "Tool1" / "2.0.0" / "Linux" / "x64")
        fs.create_file(tools_dir / "Tool1" / "Tool1.env")

        # Tool2 simple structure
        fs.create_dir(tools_dir / "Tool2")
        fs.create_file(tools_dir / "Tool2" / "Tool2.env")

        # Generate manifest
        manifest = _GenerateManifest(tools_dir)

        # Write to YAML
        output_path = Path("/output/manifest.yaml")
        WriteManifestYaml(manifest, output_path)

        # Verify
        with output_path.open() as f:
            data = yaml.safe_load(f)

        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "Tool1"
        assert data["tools"][1]["name"] == "Tool2"

        # Tool1 should have 3 configurations:
        # - v1.0.0 Linux/x64
        # - v1.0.0 Windows/x64
        # - v2.0.0 Linux/x64
        tool1_configs = data["tools"][0]["configurations"]
        assert len(tool1_configs) == 3
        versions = [c["version"] for c in tool1_configs]
        assert versions.count("1.0.0") == 2
        assert versions.count("2.0.0") == 1
