import platform
import sys

from pathlib import Path
from typing import cast

from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from semantic_version import Version as SemVer

from dbrownell_ToolsDirectory import ToolInfo


# ----------------------------------------------------------------------
class TestOperatingSystemType:
    # ----------------------------------------------------------------------
    def test_Calculate(self) -> None:
        platform = sys.platform

        if platform.startswith("linux"):
            expected = ToolInfo.OperatingSystemType.Linux
        elif platform.startswith("darwin"):
            expected = ToolInfo.OperatingSystemType.MacOS
        elif platform.startswith("win32"):
            expected = ToolInfo.OperatingSystemType.Windows

        assert ToolInfo.OperatingSystemType.Calculate() == expected

    # ----------------------------------------------------------------------
    def test_StringMap(self) -> None:
        results = ToolInfo.OperatingSystemType.Linux.string_map

        assert results == {
            "Windows": ToolInfo.OperatingSystemType.Windows,
            "MacOS": ToolInfo.OperatingSystemType.MacOS,
            "Linux": ToolInfo.OperatingSystemType.Linux,
            "Generic": "Generic",
        }


# ----------------------------------------------------------------------
class TestArchitectureType:
    # ----------------------------------------------------------------------
    def test_Calculate(self) -> None:
        architecture = platform.machine().lower()

        if architecture == "arm64":
            expected = ToolInfo.ArchitectureType.ARM64
        else:
            expected = ToolInfo.ArchitectureType.x64

        assert ToolInfo.ArchitectureType.Calculate() == expected

    # ----------------------------------------------------------------------
    def test_StringMap(self) -> None:
        results = ToolInfo.ArchitectureType.x64.string_map

        assert results == {
            "x64": ToolInfo.ArchitectureType.x64,
            "x86": ToolInfo.ArchitectureType.x86,
            "ARM64": ToolInfo.ArchitectureType.ARM64,
            "ARM": ToolInfo.ArchitectureType.ARM,
            "Generic": "Generic",
        }


# ----------------------------------------------------------------------
class TestGetToolInfos:
    # ----------------------------------------------------------------------
    def test_Standard(self, fs):
        operating_system = ToolInfo.OperatingSystemType.Calculate()
        operating_system_str = operating_system.name

        architecture = ToolInfo.ArchitectureType.Calculate()
        architecture_str = architecture.name

        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/bin/file.txt")
        fs.create_file("/Tools/Tool3/1.0.0/file.txt")
        fs.create_file("/Tools/Tool4/v2.3.4/file.txt")
        fs.create_file(f"/Tools/Tool5/1.0.0/{operating_system_str}/file.txt")
        fs.create_file(f"/Tools/Tool6/1.0.0/{operating_system_str}/bin/file.txt")
        fs.create_file(f"/Tools/Tool7/1.0.0/{operating_system_str}/{architecture_str}/file.txt")
        fs.create_file(f"/Tools/Tool8/1.0.0/{operating_system_str}/{architecture_str}/bin/file.txt")
        fs.create_file("/Tools/Tool9/1.0.0/Generic/file.txt")
        fs.create_file("/Tools/Tool10/1.0.0/Generic/bin/file.txt")
        fs.create_file(f"/Tools/Tool11/1.0.0/Generic/{architecture_str}/file.txt")
        fs.create_file(f"/Tools/Tool12/1.0.0/Generic/{architecture_str}/bin/file.txt")
        fs.create_file(f"/Tools/Tool13/{operating_system_str}/file.txt")
        fs.create_file(f"/Tools/Tool14/{operating_system_str}/bin/file.txt")
        fs.create_file(f"/Tools/Tool15/{operating_system_str}/{architecture_str}/file.txt")
        fs.create_file(f"/Tools/Tool16/{operating_system_str}/{architecture_str}/bin/file.txt")
        fs.create_file("/Tools/not_a_tool")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                None,
                None,
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
            ),
            ToolInfo.ToolInfo(
                "Tool2",
                None,
                None,
                None,
                Path("/Tools/Tool2"),
                Path("/Tools/Tool2"),
                Path("/Tools/Tool2/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool3",
                SemVer("1.0.0"),
                None,
                None,
                Path("/Tools/Tool3"),
                Path("/Tools/Tool3/1.0.0"),
                Path("/Tools/Tool3/1.0.0"),
            ),
            ToolInfo.ToolInfo(
                "Tool4",
                SemVer("2.3.4"),
                None,
                None,
                Path("/Tools/Tool4"),
                Path("/Tools/Tool4/v2.3.4"),
                Path("/Tools/Tool4/v2.3.4"),
            ),
            ToolInfo.ToolInfo(
                "Tool5",
                SemVer("1.0.0"),
                operating_system,
                None,
                Path("/Tools/Tool5"),
                Path(f"/Tools/Tool5/1.0.0/{operating_system_str}"),
                Path(f"/Tools/Tool5/1.0.0/{operating_system_str}"),
            ),
            ToolInfo.ToolInfo(
                "Tool6",
                SemVer("1.0.0"),
                operating_system,
                None,
                Path("/Tools/Tool6"),
                Path(f"/Tools/Tool6/1.0.0/{operating_system_str}"),
                Path(f"/Tools/Tool6/1.0.0/{operating_system_str}/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool7",
                SemVer("1.0.0"),
                operating_system,
                architecture,
                Path("/Tools/Tool7"),
                Path(f"/Tools/Tool7/1.0.0/{operating_system_str}/{architecture_str}"),
                Path(f"/Tools/Tool7/1.0.0/{operating_system_str}/{architecture_str}"),
            ),
            ToolInfo.ToolInfo(
                "Tool8",
                SemVer("1.0.0"),
                operating_system,
                architecture,
                Path("/Tools/Tool8"),
                Path(f"/Tools/Tool8/1.0.0/{operating_system_str}/{architecture_str}"),
                Path(f"/Tools/Tool8/1.0.0/{operating_system_str}/{architecture_str}/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool9",
                SemVer("1.0.0"),
                "Generic",
                None,
                Path("/Tools/Tool9"),
                Path("/Tools/Tool9/1.0.0/Generic"),
                Path("/Tools/Tool9/1.0.0/Generic"),
            ),
            ToolInfo.ToolInfo(
                "Tool10",
                SemVer("1.0.0"),
                "Generic",
                None,
                Path("/Tools/Tool10"),
                Path("/Tools/Tool10/1.0.0/Generic"),
                Path("/Tools/Tool10/1.0.0/Generic/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool11",
                SemVer("1.0.0"),
                "Generic",
                architecture,
                Path("/Tools/Tool11"),
                Path(f"/Tools/Tool11/1.0.0/Generic/{architecture_str}"),
                Path(f"/Tools/Tool11/1.0.0/Generic/{architecture_str}"),
            ),
            ToolInfo.ToolInfo(
                "Tool12",
                SemVer("1.0.0"),
                "Generic",
                architecture,
                Path("/Tools/Tool12"),
                Path(f"/Tools/Tool12/1.0.0/Generic/{architecture_str}"),
                Path(f"/Tools/Tool12/1.0.0/Generic/{architecture_str}/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool13",
                None,
                operating_system,
                None,
                Path("/Tools/Tool13"),
                Path(f"/Tools/Tool13/{operating_system_str}"),
                Path(f"/Tools/Tool13/{operating_system_str}"),
            ),
            ToolInfo.ToolInfo(
                "Tool14",
                None,
                operating_system,
                None,
                Path("/Tools/Tool14"),
                Path(f"/Tools/Tool14/{operating_system_str}"),
                Path(f"/Tools/Tool14/{operating_system_str}/bin"),
            ),
            ToolInfo.ToolInfo(
                "Tool15",
                None,
                operating_system,
                architecture,
                Path("/Tools/Tool15"),
                Path(f"/Tools/Tool15/{operating_system_str}/{architecture_str}"),
                Path(f"/Tools/Tool15/{operating_system_str}/{architecture_str}"),
            ),
            ToolInfo.ToolInfo(
                "Tool16",
                None,
                operating_system,
                architecture,
                Path("/Tools/Tool16"),
                Path(f"/Tools/Tool16/{operating_system_str}/{architecture_str}"),
                Path(f"/Tools/Tool16/{operating_system_str}/{architecture_str}/bin"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_Includes(self, fs):
        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/file.txt")
        fs.create_file("/Tools/Tool3/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            {"Tool1", "Tool3"},
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                None,
                None,
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
            ),
            ToolInfo.ToolInfo(
                "Tool3",
                None,
                None,
                None,
                Path("/Tools/Tool3"),
                Path("/Tools/Tool3"),
                Path("/Tools/Tool3"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_Excludes(self, fs):
        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/file.txt")
        fs.create_file("/Tools/Tool3/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            {"Tool2"},
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                None,
                None,
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1"),
            ),
            ToolInfo.ToolInfo(
                "Tool3",
                None,
                None,
                None,
                Path("/Tools/Tool3"),
                Path("/Tools/Tool3"),
                Path("/Tools/Tool3"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_LatestVersion(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                SemVer("2.0.0"),
                None,
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1/2.0.0"),
                Path("/Tools/Tool1/2.0.0"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_ExplicitVersion(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {"Tool1": ToolInfo.SemVer.coerce("1.5.0")},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                SemVer("1.5.0"),
                None,
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1/1.5.0"),
                Path("/Tools/Tool1/1.5.0"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_ExplicitVersionInvalid(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {"Tool1": ToolInfo.SemVer.coerce("3.0.0")},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path("/Tools/Tool1"))

        assert f"No directory found for version '3.0.0' for the tool 'Tool1' in '{tool_dir}'." in output

    # ----------------------------------------------------------------------
    def test_GenericOperatingSystem(self, fs):
        not_this_operating_system = next(
            operating_system
            for operating_system in ToolInfo.OperatingSystemType
            if operating_system != ToolInfo.OperatingSystemType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_operating_system.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                None,
                "Generic",
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1/Generic"),
                Path("/Tools/Tool1/Generic"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_GenericOperatingSystemNoGenerics(self, fs):
        not_this_operating_system = next(
            operating_system
            for operating_system in ToolInfo.OperatingSystemType
            if operating_system != ToolInfo.OperatingSystemType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_operating_system.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
            no_generic_operating_systems=True,
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path("/Tools/Tool1"))

        assert (
            f"No directory found for '{ToolInfo.OperatingSystemType.Calculate().name}' for the tool 'Tool1' in '{tool_dir}'."
            in output
        )

    # ----------------------------------------------------------------------
    def test_GenericArchitecture(self, fs):
        not_this_architecture = next(
            architecture
            for architecture in ToolInfo.ArchitectureType
            if architecture != ToolInfo.ArchitectureType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_architecture.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
        )

        assert results == [
            ToolInfo.ToolInfo(
                "Tool1",
                None,
                "Generic",
                None,
                Path("/Tools/Tool1"),
                Path("/Tools/Tool1/Generic"),
                Path("/Tools/Tool1/Generic"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_GenericArchitectureNoGenerics(self, fs):
        this_operating_system = ToolInfo.OperatingSystemType.Calculate().name

        not_this_architecture = next(
            architecture
            for architecture in ToolInfo.ArchitectureType
            if architecture != ToolInfo.ArchitectureType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{this_operating_system}/{not_this_architecture.name}/file.txt")
        fs.create_file(f"/Tools/Tool1/{this_operating_system}/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = ToolInfo.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            ToolInfo.OperatingSystemType.Calculate(),
            ToolInfo.ArchitectureType.Calculate(),
            no_generic_architectures=True,
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path(f"/Tools/Tool1/{this_operating_system}"))

        assert (
            f"No directory found for '{ToolInfo.ArchitectureType.Calculate().name}' for the tool 'Tool1' in '{tool_dir}'."
            in output
        )
