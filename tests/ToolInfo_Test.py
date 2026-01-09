# noqa: D100
import platform
import sys

from pathlib import Path
from unittest.mock import patch

import pytest

from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from pyfakefs.fake_filesystem import FakeFilesystem
from semantic_version import Version as SemVer

from dbrownell_ToolsDirectory.ToolInfo import (
    ArchitectureType,
    GenerateToolInfos,
    GetAllToolInfos,
    OperatingSystemType,
    ToolInfo,
)


# ----------------------------------------------------------------------
class TestOperatingSystemType:
    """Tests for OperatingSystemType enum."""

    # ----------------------------------------------------------------------
    class TestCalculate:
        # ----------------------------------------------------------------------
        def test_CalculateLinux(self) -> None:
            with patch.object(sys, "platform", "linux"):
                assert OperatingSystemType.Calculate() == OperatingSystemType.Linux

        # ----------------------------------------------------------------------
        def test_CalculateLinux2(self) -> None:
            with patch.object(sys, "platform", "linux2"):
                assert OperatingSystemType.Calculate() == OperatingSystemType.Linux

        # ----------------------------------------------------------------------
        def test_CalculateMacOS(self) -> None:
            with patch.object(sys, "platform", "darwin"):
                assert OperatingSystemType.Calculate() == OperatingSystemType.MacOS

        # ----------------------------------------------------------------------
        def test_CalculateWindows(self) -> None:
            with patch.object(sys, "platform", "win32"):
                assert OperatingSystemType.Calculate() == OperatingSystemType.Windows

        # ----------------------------------------------------------------------
        def test_CalculateUnsupportedPlatform(self) -> None:
            with patch.object(sys, "platform", "freebsd"):
                with pytest.raises(Exception, match="Unsupported platform"):
                    OperatingSystemType.Calculate()

    # ----------------------------------------------------------------------
    class TestStringMap:
        # ----------------------------------------------------------------------
        def test_StringMapContainsAllEnumValues(self) -> None:
            string_map = OperatingSystemType.StringMap()

            assert string_map["Linux"] == OperatingSystemType.Linux
            assert string_map["MacOS"] == OperatingSystemType.MacOS
            assert string_map["Windows"] == OperatingSystemType.Windows

        # ----------------------------------------------------------------------
        def test_StringMapContainsGeneric(self) -> None:
            string_map = OperatingSystemType.StringMap()

            assert string_map["Generic"] == "Generic"


# ----------------------------------------------------------------------
class TestArchitectureType:
    """Tests for ArchitectureType enum."""

    # ----------------------------------------------------------------------
    class TestCalculate:
        # ----------------------------------------------------------------------
        def test_CalculateARM64(self) -> None:
            with patch.object(platform, "machine", return_value="arm64"):
                assert ArchitectureType.Calculate() == ArchitectureType.ARM64

        # ----------------------------------------------------------------------
        def test_CalculateARM(self) -> None:
            with patch.object(platform, "machine", return_value="amd"):
                assert ArchitectureType.Calculate() == ArchitectureType.ARM

        # ----------------------------------------------------------------------
        def test_CalculateX64_x86_64(self) -> None:
            with patch.object(platform, "machine", return_value="x86_64"):
                with patch.object(sys, "maxsize", 2**33):  # 64-bit
                    assert ArchitectureType.Calculate() == ArchitectureType.x64

        # ----------------------------------------------------------------------
        def test_CalculateX64_amd64(self) -> None:
            with patch.object(platform, "machine", return_value="amd64"):
                with patch.object(sys, "maxsize", 2**33):  # 64-bit
                    assert ArchitectureType.Calculate() == ArchitectureType.x64

        # ----------------------------------------------------------------------
        def test_CalculateX86(self) -> None:
            with patch.object(platform, "machine", return_value="x86_64"):
                with patch.object(sys, "maxsize", 2**31):  # 32-bit
                    assert ArchitectureType.Calculate() == ArchitectureType.x86

        # ----------------------------------------------------------------------
        def test_CalculateUnsupportedArchitecture(self) -> None:
            with patch.object(platform, "machine", return_value="mips"):
                with pytest.raises(Exception, match="Unsupported architecture"):
                    ArchitectureType.Calculate()

    # ----------------------------------------------------------------------
    class TestStringMap:
        # ----------------------------------------------------------------------
        def test_StringMapContainsAllEnumValues(self) -> None:
            string_map = ArchitectureType.StringMap()

            assert string_map["x64"] == ArchitectureType.x64
            assert string_map["x86"] == ArchitectureType.x86
            assert string_map["ARM64"] == ArchitectureType.ARM64
            assert string_map["ARM"] == ArchitectureType.ARM

        # ----------------------------------------------------------------------
        def test_StringMapContainsGeneric(self) -> None:
            string_map = ArchitectureType.StringMap()

            assert string_map["Generic"] == "Generic"


# ----------------------------------------------------------------------
class TestToolInfoDataclass:
    """Tests for ToolInfo dataclass."""

    # ----------------------------------------------------------------------
    class TestGeneratePotentialEnvFiles:
        # ----------------------------------------------------------------------
        def test_SimpleToolNoVersionNoOsNoArch(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=None,
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1"),
                binary_directory=Path("/tools/Tool1"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [Path("/tools/Tool1/Tool1.env")]

        # ----------------------------------------------------------------------
        def test_CustomFileExtension(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=None,
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1"),
                binary_directory=Path("/tools/Tool1"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles(file_extension=".config"))

            assert env_files == [Path("/tools/Tool1/Tool1.config")]

        # ----------------------------------------------------------------------
        def test_WithVersionOnly(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=SemVer("1.0.0"),
                operating_system=None,
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/1.0.0"),
                binary_directory=Path("/tools/Tool1/1.0.0"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-v1.0.0.env"),
                # Version level files
                Path("/tools/Tool1/1.0.0/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithOSEnumOnly(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=OperatingSystemType.Linux,
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/Linux"),
                binary_directory=Path("/tools/Tool1/Linux"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-Linux.env"),
                # OS level files
                Path("/tools/Tool1/Linux/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithOSGenericOnly(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system="Generic",
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/Generic"),
                binary_directory=Path("/tools/Tool1/Generic"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-Generic.env"),
                # OS level files
                Path("/tools/Tool1/Generic/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithArchEnumOnly(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=None,
                architecture=ArchitectureType.x64,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/x64"),
                binary_directory=Path("/tools/Tool1/x64"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-x64.env"),
                # Arch level files
                Path("/tools/Tool1/x64/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithArchGenericOnly(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=None,
                architecture="Generic",
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/Generic"),
                binary_directory=Path("/tools/Tool1/Generic"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-Generic.env"),
                # Arch level files
                Path("/tools/Tool1/Generic/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithVersionAndOS(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=SemVer("1.0.0"),
                operating_system=OperatingSystemType.Linux,
                architecture=None,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/1.0.0/Linux"),
                binary_directory=Path("/tools/Tool1/1.0.0/Linux"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-v1.0.0.env"),
                Path("/tools/Tool1/Tool1-Linux.env"),
                Path("/tools/Tool1/Tool1-v1.0.0-Linux.env"),
                # Version level files
                Path("/tools/Tool1/1.0.0/Tool1.env"),
                Path("/tools/Tool1/1.0.0/Tool1-Linux.env"),
                # OS level files
                Path("/tools/Tool1/1.0.0/Linux/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithVersionOSAndArch(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=SemVer("1.0.0"),
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/1.0.0/Linux/x64"),
                binary_directory=Path("/tools/Tool1/1.0.0/Linux/x64/bin"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-v1.0.0.env"),
                Path("/tools/Tool1/Tool1-Linux.env"),
                Path("/tools/Tool1/Tool1-v1.0.0-Linux.env"),
                Path("/tools/Tool1/Tool1-x64.env"),
                Path("/tools/Tool1/Tool1-v1.0.0-x64.env"),
                Path("/tools/Tool1/Tool1-Linux-x64.env"),
                Path("/tools/Tool1/Tool1-v1.0.0-Linux-x64.env"),
                # Version level files
                Path("/tools/Tool1/1.0.0/Tool1.env"),
                Path("/tools/Tool1/1.0.0/Tool1-Linux.env"),
                Path("/tools/Tool1/1.0.0/Tool1-x64.env"),
                Path("/tools/Tool1/1.0.0/Tool1-Linux-x64.env"),
                # OS level files
                Path("/tools/Tool1/1.0.0/Linux/Tool1.env"),
                Path("/tools/Tool1/1.0.0/Linux/Tool1-x64.env"),
                # Architecture level files
                Path("/tools/Tool1/1.0.0/Linux/x64/Tool1.env"),
            ]

        # ----------------------------------------------------------------------
        def test_WithOSAndArchNoVersion(self) -> None:
            tool_info = ToolInfo(
                name="Tool1",
                version=None,
                operating_system=OperatingSystemType.Windows,
                architecture=ArchitectureType.x64,
                root_directory=Path("/tools/Tool1"),
                versioned_directory=Path("/tools/Tool1/Windows/x64"),
                binary_directory=Path("/tools/Tool1/Windows/x64"),
            )

            env_files = list(tool_info.GeneratePotentialEnvFiles())

            assert env_files == [
                # Root level files
                Path("/tools/Tool1/Tool1.env"),
                Path("/tools/Tool1/Tool1-Windows.env"),
                Path("/tools/Tool1/Tool1-x64.env"),
                Path("/tools/Tool1/Tool1-Windows-x64.env"),
                # OS level files
                Path("/tools/Tool1/Windows/Tool1.env"),
                Path("/tools/Tool1/Windows/Tool1-x64.env"),
                # Architecture level files
                Path("/tools/Tool1/Windows/x64/Tool1.env"),
            ]


# ----------------------------------------------------------------------
class TestGenerateToolInfos:
    """Tests for GenerateToolInfos function."""

    # ----------------------------------------------------------------------
    class TestDirectoryStructureVariations:
        # ----------------------------------------------------------------------
        def test_FlatToolNoHierarchy(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_file("/tools/Tool1/executable.exe")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].name == "Tool1"
            assert tool_infos[0].version is None
            assert tool_infos[0].operating_system is None
            assert tool_infos[0].architecture is None
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1")

        # ----------------------------------------------------------------------
        def test_WithBinSubdirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/bin")
            fs.create_file("/tools/Tool1/bin/executable.exe")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/bin")

        # ----------------------------------------------------------------------
        def test_WithoutBinSubdirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1")

    # ----------------------------------------------------------------------
    class TestVersionDirectoryHandling:
        # ----------------------------------------------------------------------
        def test_SemVerDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].version == SemVer("1.0.0")
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/1.0.0")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/1.0.0")

        # ----------------------------------------------------------------------
        def test_SemVerWithVPrefix(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/v1.0.0")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].version == SemVer("1.0.0")
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/v1.0.0")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/v1.0.0")

        # ----------------------------------------------------------------------
        def test_MultipleVersionsFilterLatest(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/2.0.0")
            fs.create_dir("/tools/Tool1/1.5.0")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter="latest",
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].version == SemVer("2.0.0")
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/2.0.0")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/2.0.0")

        # ----------------------------------------------------------------------
        def test_MultipleVersionsFilterSpecific(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/2.0.0")
            fs.create_dir("/tools/Tool1/1.5.0")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=SemVer("1.5.0"),
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].version == SemVer("1.5.0")
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/1.5.0")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/1.5.0")

        # ----------------------------------------------------------------------
        def test_MultipleVersionsNoFilter(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/2.0.0")
            fs.create_dir("/tools/Tool1/1.5.0")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 3
            versions = [ti.version for ti in tool_infos]
            assert SemVer("1.0.0") in versions
            assert SemVer("1.5.0") in versions
            assert SemVer("2.0.0") in versions

            # All should have the same root_directory
            for ti in tool_infos:
                assert ti.root_directory == Path("/tools/Tool1")
                assert ti.versioned_directory == Path("/tools/Tool1") / str(ti.version)
                assert ti.binary_directory == Path("/tools/Tool1") / str(ti.version)

        # ----------------------------------------------------------------------
        def test_NonVersionDirectoryIgnored(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/docs")  # Not a version

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter="latest",
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].version == SemVer("1.0.0")
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/1.0.0")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/1.0.0")

        # ----------------------------------------------------------------------
        def test_VersionNotFound(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")

            with pytest.raises(
                ValueError,
                match=r"^No directory found for version '9\.9\.9' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=SemVer("9.9.9"),
                        operating_system_filter=None,
                        architecture_filter=None,
                    )
                )

    # ----------------------------------------------------------------------
    class TestOperatingSystemDirectoryHandling:
        # ----------------------------------------------------------------------
        def test_LinuxDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Linux")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == OperatingSystemType.Linux
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Linux")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Linux")

        # ----------------------------------------------------------------------
        def test_MacOSDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/MacOS")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == OperatingSystemType.MacOS
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/MacOS")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/MacOS")

        # ----------------------------------------------------------------------
        def test_WindowsDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Windows")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == OperatingSystemType.Windows
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Windows")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Windows")

        # ----------------------------------------------------------------------
        def test_GenericOSDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Generic")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == "Generic"
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Generic")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Generic")

        # ----------------------------------------------------------------------
        def test_OSFilterMatchesSpecific(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Linux")
            fs.create_dir("/tools/Tool1/Windows")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == OperatingSystemType.Linux
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Linux")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Linux")

        # ----------------------------------------------------------------------
        def test_OSFilterWithGenericFallback(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Generic")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=None,
                    allow_generic_operating_system=True,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == "Generic"
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Generic")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Generic")

        # ----------------------------------------------------------------------
        def test_OSFilterNoMatchNoFallback(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Windows")

            with pytest.raises(
                ValueError,
                match=r"^No directory found for 'Linux' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=None,
                        operating_system_filter=OperatingSystemType.Linux,
                        architecture_filter=None,
                        allow_generic_operating_system=False,
                    )
                )

        # ----------------------------------------------------------------------
        def test_NoOSDirectories(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_file("/tools/Tool1/executable.exe")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system is None
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1")

        # ----------------------------------------------------------------------
        def test_UnknownOSDirectoryIgnored(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/UnknownOS")
            fs.create_dir("/tools/Tool1/Linux")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            # UnknownOS is not a valid OS, so it's ignored
            assert len(tool_infos) == 1
            assert tool_infos[0].operating_system == OperatingSystemType.Linux
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Linux")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Linux")

    # ----------------------------------------------------------------------
    class TestArchitectureDirectoryHandling:
        # ----------------------------------------------------------------------
        def test_X64Directory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/x64")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == ArchitectureType.x64
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/x64")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/x64")

        # ----------------------------------------------------------------------
        def test_X86Directory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/x86")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == ArchitectureType.x86
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/x86")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/x86")

        # ----------------------------------------------------------------------
        def test_ARM64Directory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/ARM64")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == ArchitectureType.ARM64
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/ARM64")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/ARM64")

        # ----------------------------------------------------------------------
        def test_ARMDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/ARM")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == ArchitectureType.ARM
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/ARM")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/ARM")

        # ----------------------------------------------------------------------
        def test_GenericArchDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Linux/Generic")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == "Generic"
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Linux/Generic")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Linux/Generic")

        # ----------------------------------------------------------------------
        def test_ArchFilterMatchesSpecific(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/x64")
            fs.create_dir("/tools/Tool1/ARM64")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=ArchitectureType.x64,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == ArchitectureType.x64
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/x64")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/x64")

        # ----------------------------------------------------------------------
        def test_ArchFilterWithGenericFallback(self, fs: FakeFilesystem) -> None:
            # Need to have OS-specific directory first, then Generic arch inside
            fs.create_dir("/tools/Tool1/Linux/Generic")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=ArchitectureType.x64,
                    allow_generic_architecture=True,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture == "Generic"
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1/Linux/Generic")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1/Linux/Generic")

        # ----------------------------------------------------------------------
        def test_ArchFilterNoMatchNoFallback(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/ARM64")

            with pytest.raises(
                ValueError,
                match=r"^No directory found for 'x64' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=None,
                        operating_system_filter=None,
                        architecture_filter=ArchitectureType.x64,
                        allow_generic_architecture=False,
                    )
                )

        # ----------------------------------------------------------------------
        def test_NoArchDirectories(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter=None,
                    operating_system_filter=None,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            assert tool_infos[0].architecture is None
            assert tool_infos[0].root_directory == Path("/tools/Tool1")
            assert tool_infos[0].versioned_directory == Path("/tools/Tool1")
            assert tool_infos[0].binary_directory == Path("/tools/Tool1")

    # ----------------------------------------------------------------------
    class TestFullHierarchy:
        # ----------------------------------------------------------------------
        def test_CompleteHierarchy(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0/Linux/x64/bin")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter="latest",
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=ArchitectureType.x64,
                )
            )

            assert len(tool_infos) == 1
            ti = tool_infos[0]
            assert ti.name == "Tool1"
            assert ti.version == SemVer("1.0.0")
            assert ti.operating_system == OperatingSystemType.Linux
            assert ti.architecture == ArchitectureType.x64
            assert ti.root_directory == Path("/tools/Tool1")
            assert ti.versioned_directory == Path("/tools/Tool1/1.0.0/Linux/x64")
            assert ti.binary_directory == Path("/tools/Tool1/1.0.0/Linux/x64/bin")

        # ----------------------------------------------------------------------
        def test_PartialHierarchyVersionAndOS(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0/Linux")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter="latest",
                    operating_system_filter=OperatingSystemType.Linux,
                    architecture_filter=None,
                )
            )

            assert len(tool_infos) == 1
            ti = tool_infos[0]
            assert ti.version == SemVer("1.0.0")
            assert ti.operating_system == OperatingSystemType.Linux
            assert ti.architecture is None

        # ----------------------------------------------------------------------
        def test_PartialHierarchyVersionAndArch(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0/x64")

            tool_infos = list(
                GenerateToolInfos(
                    Path("/tools/Tool1"),
                    version_filter="latest",
                    operating_system_filter=None,
                    architecture_filter=ArchitectureType.x64,
                )
            )

            assert len(tool_infos) == 1
            ti = tool_infos[0]
            assert ti.version == SemVer("1.0.0")
            assert ti.operating_system is None
            assert ti.architecture == ArchitectureType.x64


# ----------------------------------------------------------------------
class TestGetAllToolInfos:
    """Tests for GetAllToolInfos function."""

    # ----------------------------------------------------------------------
    class TestBasicFunctionality:
        # ----------------------------------------------------------------------
        def test_EmptyDirectory(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert result == []

        # ----------------------------------------------------------------------
        def test_SingleTool(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].name == "Tool1"

        # ----------------------------------------------------------------------
        def test_MultipleTools(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")
            fs.create_dir("/tools/Tool3")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 3
            names = [ti.name for ti in result]
            assert "Tool1" in names
            assert "Tool2" in names
            assert "Tool3" in names

        # ----------------------------------------------------------------------
        def test_IgnoresFiles(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_file("/tools/some_file.txt")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].name == "Tool1"

    # ----------------------------------------------------------------------
    class TestIncludeExcludeFiltering:
        # ----------------------------------------------------------------------
        def test_IncludeSpecificTool(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")
            fs.create_dir("/tools/Tool3")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools={"Tool1"},
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].name == "Tool1"

        # ----------------------------------------------------------------------
        def test_IncludeMultipleTools(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")
            fs.create_dir("/tools/Tool3")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools={"Tool1", "Tool2"},
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 2
            names = [ti.name for ti in result]
            assert "Tool1" in names
            assert "Tool2" in names

        # ----------------------------------------------------------------------
        def test_ExcludeSpecificTool(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")
            fs.create_dir("/tools/Tool3")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools={"Tool1"},
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 2
            names = [ti.name for ti in result]
            assert "Tool2" in names
            assert "Tool3" in names
            assert "Tool1" not in names

        # ----------------------------------------------------------------------
        def test_ExcludeMultipleTools(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")
            fs.create_dir("/tools/Tool3")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools={"Tool1", "Tool2"},
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].name == "Tool3"

        # ----------------------------------------------------------------------
        def test_IncludeEmptySet(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1")
            fs.create_dir("/tools/Tool2")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),  # Empty means all
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 2

    # ----------------------------------------------------------------------
    class TestVersionFiltering:
        # ----------------------------------------------------------------------
        def test_SpecificVersion(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/2.0.0")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={"Tool1": SemVer("1.0.0")},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].version == SemVer("1.0.0")

        # ----------------------------------------------------------------------
        def test_LatestVersionDefault(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/1.0.0")
            fs.create_dir("/tools/Tool1/2.0.0")
            fs.create_dir("/tools/Tool1/1.5.0")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},  # No version specified, should use latest
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].version == SemVer("2.0.0")

    # ----------------------------------------------------------------------
    class TestOSArchitectureFiltering:
        # ----------------------------------------------------------------------
        def test_MatchCurrentOS(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Linux")
            fs.create_dir("/tools/Tool1/Windows")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].operating_system == OperatingSystemType.Linux

        # ----------------------------------------------------------------------
        def test_MatchCurrentArchitecture(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/x64")
            fs.create_dir("/tools/Tool1/ARM64")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
            )

            assert len(result) == 1
            assert result[0].architecture == ArchitectureType.x64

        # ----------------------------------------------------------------------
        def test_GenericOSFallbackEnabled(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Generic")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
                allow_generic_operating_systems=True,
            )

            assert len(result) == 1
            assert result[0].operating_system == "Generic"

        # ----------------------------------------------------------------------
        def test_GenericOSFallbackDisabled(self, fs: FakeFilesystem) -> None:
            # When there are OS directories but none match and Generic is not allowed,
            # an exception is raised by GenerateToolInfos
            fs.create_dir("/tools/Tool1/Windows")  # Only Windows, no Linux or Generic

            # GenerateToolInfos will raise ValueError because no matching OS dir found
            with pytest.raises(
                ValueError,
                match=r"^No directory found for 'Linux' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=None,
                        operating_system_filter=OperatingSystemType.Linux,
                        architecture_filter=None,
                        allow_generic_operating_system=False,
                    )
                )

        # ----------------------------------------------------------------------
        def test_GenericArchFallbackEnabled(self, fs: FakeFilesystem) -> None:
            fs.create_dir("/tools/Tool1/Generic")

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
                allow_generic_architectures=True,
            )

            assert len(result) == 1

        # ----------------------------------------------------------------------
        def test_GenericArchFallbackDisabled(self, fs: FakeFilesystem) -> None:
            # When there are arch directories but none match and Generic is not allowed,
            # an exception is raised by GenerateToolInfos
            fs.create_dir("/tools/Tool1/Linux/ARM64")  # Only ARM64, no x64 or Generic

            # GenerateToolInfos will raise ValueError because no matching arch dir found
            with pytest.raises(
                ValueError,
                match=r"^No directory found for 'x64' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1[/\\]Linux'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=None,
                        operating_system_filter=OperatingSystemType.Linux,
                        architecture_filter=ArchitectureType.x64,
                        allow_generic_architecture=False,
                    )
                )

    # ----------------------------------------------------------------------
    class TestErrorHandling:
        # ----------------------------------------------------------------------
        def test_NoValidConfigurations(self, fs: FakeFilesystem) -> None:
            # When there are OS directories but none match and Generic is not allowed,
            # an exception is raised by GenerateToolInfos
            fs.create_dir("/tools/Tool1/Windows")  # Only Windows, no Linux

            # GenerateToolInfos will raise ValueError because no matching OS dir found
            with pytest.raises(
                ValueError,
                match=r"^No directory found for 'Linux' for the tool 'Tool1' in '[/\\]tools[/\\]Tool1'\.$",
            ):
                list(
                    GenerateToolInfos(
                        Path("/tools/Tool1"),
                        version_filter=None,
                        operating_system_filter=OperatingSystemType.Linux,
                        architecture_filter=None,
                        allow_generic_operating_system=False,
                    )
                )

        # ----------------------------------------------------------------------
        def test_NoToolsFoundDueToErrors(self, fs: FakeFilesystem) -> None:
            # Create tool directories that will fail to produce valid ToolInfos
            # because the OS directories don't match and Generic fallback is disabled
            fs.create_dir("/tools/Tool1/Windows")  # Only Windows, requesting Linux
            fs.create_dir("/tools/Tool2/MacOS")  # Only MacOS, requesting Linux

            dm_and_sink = iter(GenerateDoneManagerAndContent())

            result = GetAllToolInfos(
                next(dm_and_sink),
                Path("/tools"),
                include_tools=set(),
                exclude_tools=set(),
                tool_versions={},
                operating_system=OperatingSystemType.Linux,
                architecture=ArchitectureType.x64,
                allow_generic_operating_systems=False,
            )

            # No tools should be returned because all failed
            assert result == []

            # Verify that error messages were written for both tools
            output = next(dm_and_sink)
            assert "No directory found for 'Linux' for the tool 'Tool1'" in output
            assert "No directory found for 'Linux' for the tool 'Tool2'" in output


# ----------------------------------------------------------------------
class TestIntegrationAndEdgeCases:
    """Integration and edge case tests."""

    # ----------------------------------------------------------------------
    def test_DeeplyNestedBinDirectory(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/Tool1/1.0.0/Linux/x64/bin")
        fs.create_file("/tools/Tool1/1.0.0/Linux/x64/bin/tool.exe")

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter="latest",
                operating_system_filter=OperatingSystemType.Linux,
                architecture_filter=ArchitectureType.x64,
            )
        )

        assert len(tool_infos) == 1
        assert tool_infos[0].binary_directory == Path("/tools/Tool1/1.0.0/Linux/x64/bin")

    # ----------------------------------------------------------------------
    def test_ToolNameWithSpecialChars(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/my-tool_v2")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        result = GetAllToolInfos(
            next(dm_and_sink),
            Path("/tools"),
            include_tools=set(),
            exclude_tools=set(),
            tool_versions={},
            operating_system=OperatingSystemType.Linux,
            architecture=ArchitectureType.x64,
        )

        assert len(result) == 1
        assert result[0].name == "my-tool_v2"

    # ----------------------------------------------------------------------
    def test_EmptyToolDirectory(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/Tool1")

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter=None,
                operating_system_filter=None,
                architecture_filter=None,
            )
        )

        assert len(tool_infos) == 1
        assert tool_infos[0].version is None
        assert tool_infos[0].operating_system is None
        assert tool_infos[0].architecture is None

    # ----------------------------------------------------------------------
    def test_CoercibleVersions(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/Tool1/1.0")  # Partial version

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter=None,
                operating_system_filter=None,
                architecture_filter=None,
            )
        )

        assert len(tool_infos) == 1
        assert tool_infos[0].version == SemVer("1.0.0")

    # ----------------------------------------------------------------------
    def test_CaseSensitiveOSDirectories(self, fs: FakeFilesystem) -> None:
        # On Windows, the fake filesystem is case-insensitive, so we test
        # that only the correctly-cased directory is recognized by StringMap
        fs.create_dir("/tools/Tool1/Linux")  # correct case - recognized as OS
        fs.create_dir("/tools/Tool1/other")  # other directory - not recognized

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter=None,
                operating_system_filter=OperatingSystemType.Linux,
                architecture_filter=None,
            )
        )

        assert len(tool_infos) == 1
        assert tool_infos[0].operating_system == OperatingSystemType.Linux

    # ----------------------------------------------------------------------
    def test_MultipleVersionsSortedDescending(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/Tool1/1.0.0")
        fs.create_dir("/tools/Tool1/2.0.0")
        fs.create_dir("/tools/Tool1/1.5.0")
        fs.create_dir("/tools/Tool1/0.9.0")

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter=None,
                operating_system_filter=None,
                architecture_filter=None,
            )
        )

        # Versions should be sorted descending
        versions = [ti.version for ti in tool_infos]
        assert versions[0] == SemVer("2.0.0")
        assert versions[1] == SemVer("1.5.0")
        assert versions[2] == SemVer("1.0.0")
        assert versions[3] == SemVer("0.9.0")

    # ----------------------------------------------------------------------
    def test_MixedVersionAndNonVersionDirs(self, fs: FakeFilesystem) -> None:
        fs.create_dir("/tools/Tool1/1.0.0")
        fs.create_dir("/tools/Tool1/2.0.0")
        fs.create_dir("/tools/Tool1/docs")
        fs.create_dir("/tools/Tool1/config")

        tool_infos = list(
            GenerateToolInfos(
                Path("/tools/Tool1"),
                version_filter=None,
                operating_system_filter=None,
                architecture_filter=None,
            )
        )

        # Should only get versioned directories
        assert len(tool_infos) == 2
        versions = [ti.version for ti in tool_infos]
        assert SemVer("1.0.0") in versions
        assert SemVer("2.0.0") in versions
