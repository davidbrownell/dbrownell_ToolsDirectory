import platform
import sys

from pathlib import Path
from typing import cast

from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from dbrownell_ToolsDirectory import Lib


# ----------------------------------------------------------------------
class TestOperatingSystemType:
    # ----------------------------------------------------------------------
    def test_Calculate(self) -> None:
        platform = sys.platform

        if platform.startswith("linux"):
            expected = Lib.OperatingSystemType.Linux
        elif platform.startswith("darwin"):
            expected = Lib.OperatingSystemType.MacOS
        elif platform.startswith("win32"):
            expected = Lib.OperatingSystemType.Windows

        assert Lib.OperatingSystemType.Calculate() == expected

    # ----------------------------------------------------------------------
    def test_Strings(self) -> None:
        results = Lib.OperatingSystemType.Linux.strings

        assert results == set(
            [
                "Windows",
                "MacOS",
                "Linux",
                "Generic",
            ],
        )


# ----------------------------------------------------------------------
class TestArchitectureType:
    # ----------------------------------------------------------------------
    def test_Calculate(self) -> None:
        architecture = platform.machine().lower()

        if architecture == "arm64":
            expected = Lib.ArchitectureType.ARM64
        else:
            expected = Lib.ArchitectureType.x64

        assert Lib.ArchitectureType.Calculate() == expected

    # ----------------------------------------------------------------------
    def test_Strings(self) -> None:
        results = Lib.ArchitectureType.x64.strings

        assert results == set(
            [
                "x64",
                "x86",
                "ARM64",
                "ARM",
                "Generic",
            ],
        )


# ----------------------------------------------------------------------
class TestGetToolInfos:
    # ----------------------------------------------------------------------
    def test_Standard(self, fs):
        operating_system = Lib.OperatingSystemType.Calculate().name
        architecture = Lib.ArchitectureType.Calculate().name

        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/bin/file.txt")
        fs.create_file("/Tools/Tool3/1.0.0/file.txt")
        fs.create_file("/Tools/Tool4/v2.3.4/file.txt")
        fs.create_file(f"/Tools/Tool5/1.0.0/{operating_system}/file.txt")
        fs.create_file(f"/Tools/Tool6/1.0.0/{operating_system}/bin/file.txt")
        fs.create_file(f"/Tools/Tool7/1.0.0/{operating_system}/{architecture}/file.txt")
        fs.create_file(f"/Tools/Tool8/1.0.0/{operating_system}/{architecture}/bin/file.txt")
        fs.create_file("/Tools/Tool9/1.0.0/Generic/file.txt")
        fs.create_file("/Tools/Tool10/1.0.0/Generic/bin/file.txt")
        fs.create_file(f"/Tools/Tool11/1.0.0/Generic/{architecture}/file.txt")
        fs.create_file(f"/Tools/Tool12/1.0.0/Generic/{architecture}/bin/file.txt")
        fs.create_file(f"/Tools/Tool13/{operating_system}/file.txt")
        fs.create_file(f"/Tools/Tool14/{operating_system}/bin/file.txt")
        fs.create_file(f"/Tools/Tool15/{operating_system}/{architecture}/file.txt")
        fs.create_file(f"/Tools/Tool16/{operating_system}/{architecture}/bin/file.txt")
        fs.create_file("/Tools/not_a_tool")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo("Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1"), Path("/Tools/Tool1")),
            Lib.ToolInfo("Tool2", Path("/Tools/Tool2"), Path("/Tools/Tool2"), Path("/Tools/Tool2/bin")),
            Lib.ToolInfo(
                "Tool3", Path("/Tools/Tool3"), Path("/Tools/Tool3/1.0.0"), Path("/Tools/Tool3/1.0.0")
            ),
            Lib.ToolInfo(
                "Tool4", Path("/Tools/Tool4"), Path("/Tools/Tool4/v2.3.4"), Path("/Tools/Tool4/v2.3.4")
            ),
            Lib.ToolInfo(
                "Tool5",
                Path("/Tools/Tool5"),
                Path(f"/Tools/Tool5/1.0.0/{operating_system}"),
                Path(f"/Tools/Tool5/1.0.0/{operating_system}"),
            ),
            Lib.ToolInfo(
                "Tool6",
                Path("/Tools/Tool6"),
                Path(f"/Tools/Tool6/1.0.0/{operating_system}"),
                Path(f"/Tools/Tool6/1.0.0/{operating_system}/bin"),
            ),
            Lib.ToolInfo(
                "Tool7",
                Path("/Tools/Tool7"),
                Path(f"/Tools/Tool7/1.0.0/{operating_system}/{architecture}"),
                Path(f"/Tools/Tool7/1.0.0/{operating_system}/{architecture}"),
            ),
            Lib.ToolInfo(
                "Tool8",
                Path("/Tools/Tool8"),
                Path(f"/Tools/Tool8/1.0.0/{operating_system}/{architecture}"),
                Path(f"/Tools/Tool8/1.0.0/{operating_system}/{architecture}/bin"),
            ),
            Lib.ToolInfo(
                "Tool9",
                Path("/Tools/Tool9"),
                Path("/Tools/Tool9/1.0.0/Generic"),
                Path("/Tools/Tool9/1.0.0/Generic"),
            ),
            Lib.ToolInfo(
                "Tool10",
                Path("/Tools/Tool10"),
                Path("/Tools/Tool10/1.0.0/Generic"),
                Path("/Tools/Tool10/1.0.0/Generic/bin"),
            ),
            Lib.ToolInfo(
                "Tool11",
                Path("/Tools/Tool11"),
                Path(f"/Tools/Tool11/1.0.0/Generic/{architecture}"),
                Path(f"/Tools/Tool11/1.0.0/Generic/{architecture}"),
            ),
            Lib.ToolInfo(
                "Tool12",
                Path("/Tools/Tool12"),
                Path(f"/Tools/Tool12/1.0.0/Generic/{architecture}"),
                Path(f"/Tools/Tool12/1.0.0/Generic/{architecture}/bin"),
            ),
            Lib.ToolInfo(
                "Tool13",
                Path("/Tools/Tool13"),
                Path(f"/Tools/Tool13/{operating_system}"),
                Path(f"/Tools/Tool13/{operating_system}"),
            ),
            Lib.ToolInfo(
                "Tool14",
                Path("/Tools/Tool14"),
                Path(f"/Tools/Tool14/{operating_system}"),
                Path(f"/Tools/Tool14/{operating_system}/bin"),
            ),
            Lib.ToolInfo(
                "Tool15",
                Path("/Tools/Tool15"),
                Path(f"/Tools/Tool15/{operating_system}/{architecture}"),
                Path(f"/Tools/Tool15/{operating_system}/{architecture}"),
            ),
            Lib.ToolInfo(
                "Tool16",
                Path("/Tools/Tool16"),
                Path(f"/Tools/Tool16/{operating_system}/{architecture}"),
                Path(f"/Tools/Tool16/{operating_system}/{architecture}/bin"),
            ),
        ]

    # ----------------------------------------------------------------------
    def test_Includes(self, fs):
        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/file.txt")
        fs.create_file("/Tools/Tool3/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            {"Tool1", "Tool3"},
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo("Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1"), Path("/Tools/Tool1")),
            Lib.ToolInfo("Tool3", Path("/Tools/Tool3"), Path("/Tools/Tool3"), Path("/Tools/Tool3")),
        ]

    # ----------------------------------------------------------------------
    def test_Excludes(self, fs):
        fs.create_file("/Tools/Tool1/file.txt")
        fs.create_file("/Tools/Tool2/file.txt")
        fs.create_file("/Tools/Tool3/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            {"Tool2"},
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo("Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1"), Path("/Tools/Tool1")),
            Lib.ToolInfo("Tool3", Path("/Tools/Tool3"), Path("/Tools/Tool3"), Path("/Tools/Tool3")),
        ]

    # ----------------------------------------------------------------------
    def test_LatestVersion(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo(
                "Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1/2.0.0"), Path("/Tools/Tool1/2.0.0")
            ),
        ]

    # ----------------------------------------------------------------------
    def test_ExplicitVersion(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {"Tool1": Lib.SemVer.coerce("1.5.0")},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo(
                "Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1/1.5.0"), Path("/Tools/Tool1/1.5.0")
            ),
        ]

    # ----------------------------------------------------------------------
    def test_ExplicitVersionInvalid(self, fs):
        fs.create_file("/Tools/Tool1/1.0.0/file.txt")
        fs.create_file("/Tools/Tool1/2.0.0/file.txt")
        fs.create_file("/Tools/Tool1/1.5.0/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {"Tool1": Lib.SemVer.coerce("3.0.0")},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path("/Tools/Tool1"))

        assert f"No directory found for version '3.0.0' for the tool 'Tool1' in '{tool_dir}'." in output

    # ----------------------------------------------------------------------
    def test_GenericOperatingSystem(self, fs):
        not_this_operating_system = next(
            operating_system
            for operating_system in Lib.OperatingSystemType
            if operating_system != Lib.OperatingSystemType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_operating_system.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo(
                "Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1/Generic"), Path("/Tools/Tool1/Generic")
            ),
        ]

    # ----------------------------------------------------------------------
    def test_GenericOperatingSystemNoGenerics(self, fs):
        not_this_operating_system = next(
            operating_system
            for operating_system in Lib.OperatingSystemType
            if operating_system != Lib.OperatingSystemType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_operating_system.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
            no_generic_operating_systems=True,
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path("/Tools/Tool1"))

        assert (
            f"No directory found for '{Lib.OperatingSystemType.Calculate().name}' for the tool 'Tool1' in '{tool_dir}'."
            in output
        )

    # ----------------------------------------------------------------------
    def test_GenericArchitecture(self, fs):
        not_this_architecture = next(
            architecture
            for architecture in Lib.ArchitectureType
            if architecture != Lib.ArchitectureType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{not_this_architecture.name}/file.txt")
        fs.create_file("/Tools/Tool1/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
        )

        assert results == [
            Lib.ToolInfo(
                "Tool1", Path("/Tools/Tool1"), Path("/Tools/Tool1/Generic"), Path("/Tools/Tool1/Generic")
            ),
        ]

    # ----------------------------------------------------------------------
    def test_GenericArchitectureNoGenerics(self, fs):
        this_operating_system = Lib.OperatingSystemType.Calculate().name

        not_this_architecture = next(
            architecture
            for architecture in Lib.ArchitectureType
            if architecture != Lib.ArchitectureType.Calculate()
        )

        fs.create_file(f"/Tools/Tool1/{this_operating_system}/{not_this_architecture.name}/file.txt")
        fs.create_file(f"/Tools/Tool1/{this_operating_system}/Generic/file.txt")

        dm_and_sink = iter(GenerateDoneManagerAndContent())

        results = Lib.GetToolInfos(
            cast(DoneManager, next(dm_and_sink)),
            Path("/Tools"),
            set(),
            set(),
            {},
            Lib.OperatingSystemType.Calculate(),
            Lib.ArchitectureType.Calculate(),
            no_generic_architectures=True,
        )

        assert results == []

        output = next(dm_and_sink)

        tool_dir = str(Path(f"/Tools/Tool1/{this_operating_system}"))

        assert (
            f"No directory found for '{Lib.ArchitectureType.Calculate().name}' for the tool 'Tool1' in '{tool_dir}'."
            in output
        )
