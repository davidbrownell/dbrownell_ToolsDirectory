import os
import re
import textwrap

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

from click.testing import Result
from dbrownell_Common.Streams.DoneManager import DoneManager
from pyfakefs.fake_filesystem import FakeFilesystem
from _pytest.monkeypatch import MonkeyPatch
from semantic_version import Version as SemVer
from typer.testing import CliRunner

from dbrownell_ToolsDirectory import __version__
from dbrownell_ToolsDirectory import __main__
from dbrownell_ToolsDirectory import ToolInfo


# ----------------------------------------------------------------------
def test_NoArgs(fs, monkeypatch):
    result, args = _Execute(fs, monkeypatch, [])

    assert result.exit_code == 0

    assert args is not None
    assert args.tool_directory
    assert args.include_tools == set()
    assert args.exclude_tools == set()
    assert args.tool_versions == dict()
    assert args.no_generic_operating_systems is False
    assert args.no_generic_architectures is False
    assert args.dm.is_verbose is False
    assert args.dm.is_debug is False


# ----------------------------------------------------------------------
def test_IncludesAndExcludes(fs, monkeypatch):
    result, args = _Execute(fs, monkeypatch, ["--include", "A", "--include", "B", "--exclude", "C"])

    assert result.exit_code == 0

    assert args is not None
    assert args.tool_directory
    assert args.include_tools == set(["A", "B"])
    assert args.exclude_tools == set(["C"])
    assert args.tool_versions == dict()
    assert args.no_generic_operating_systems is False
    assert args.no_generic_architectures is False
    assert args.dm.is_verbose is False
    assert args.dm.is_debug is False


# ----------------------------------------------------------------------
def test_ToolVersions(fs, monkeypatch):
    result, args = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "ToolA=1.2.3", "--tool-version", "ToolB=4.5.6"],
    )

    assert result.exit_code == 0

    assert args is not None
    assert args.tool_directory
    assert args.include_tools == set()
    assert args.exclude_tools == set()
    assert args.tool_versions == {
        "ToolA": SemVer("1.2.3"),
        "ToolB": SemVer("4.5.6"),
    }
    assert args.no_generic_operating_systems is False
    assert args.no_generic_architectures is False
    assert args.dm.is_verbose is False
    assert args.dm.is_debug is False


# ----------------------------------------------------------------------
def test_InvalidToolVersionString(fs, monkeypatch):
    result, args = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "InvalidToolVersionString"],
        expect_failure=True,
    )

    assert result.exit_code != 0
    assert args is None


# ----------------------------------------------------------------------
def test_InvalidToolVersionValue(fs, monkeypatch):
    result, args = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "ToolA=NotASemVer"],
        expect_failure=True,
    )

    assert result.exit_code != 0
    assert args is None


# ----------------------------------------------------------------------
def test_NoToolsFound(fs, monkeypatch):
    result, args = _Execute(fs, monkeypatch, [], tool_infos=[])

    assert result.exit_code != 0


# ----------------------------------------------------------------------
def test_Bash(fs, monkeypatch):
    output_filename = Path("output.sh")

    result, args = _Execute(fs, monkeypatch, [], output_type="bash", output_filename=output_filename)

    assert result.exit_code == 0

    assert output_filename.is_file()

    content = output_filename.read_text(encoding="utf-8")

    assert _ScrubBashOutput(content) == textwrap.dedent(
        """\
        set +v
        set +x

        [[ ":${{PATH}}:" != *":does{sep}not{sep}exist:"* ]] && export PATH="${{PATH}}:does{sep}not{sep}exist"
        true
        """,
    ).format(sep=os.path.sep)


# ----------------------------------------------------------------------
def test_Batch(fs, monkeypatch):
    output_filename = Path("output.bat")

    result, args = _Execute(fs, monkeypatch, [], output_type="batch", output_filename=output_filename)

    assert result.exit_code == 0

    assert output_filename.is_file()

    content = output_filename.read_text(encoding="utf-8")

    assert _ScrubBatchOutput(content) == textwrap.dedent(
        """\
        @echo off

        REM does{sep}not{sep}exist
        echo ";%PATH%;" | findstr /C:";does{sep}not{sep}exist;" >nul
        if %ERRORLEVEL% == 0 goto GUID_1

        set PATH=%PATH%;does{sep}not{sep}exist

        :GUID_1

        """,
    ).format(sep=os.path.sep)


# ----------------------------------------------------------------------
def test_Version():
    result = CliRunner().invoke(__main__.app, ["version"])

    assert result.exit_code == 0
    assert result.output.strip() == __version__


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class _Args:
    dm: DoneManager
    tool_directory: Path
    include_tools: set[str]
    exclude_tools: set[str]
    tool_versions: dict[str, SemVer]
    operating_system: ToolInfo.OperatingSystemType
    architecture: ToolInfo.ArchitectureType
    no_generic_operating_systems: bool
    no_generic_architectures: bool


# ----------------------------------------------------------------------
def _Execute(
    fs: FakeFilesystem,
    monkeypatch: MonkeyPatch,
    args: list[str],
    tool_infos: list[ToolInfo.ToolInfo] | None = None,
    tool_directory: Path = Path("does/not/exist"),
    output_filename: Path = Path("output.file"),
    output_type: str = "bash",
    *,
    expect_failure: bool = False,
) -> tuple[Result, _Args | None]:
    fs.create_file(tool_directory / "dummy.txt")

    if tool_infos is None:
        tool_infos = [
            ToolInfo.ToolInfo(
                "TheTool",
                None,
                None,
                None,
                tool_directory,
                tool_directory,
                tool_directory,
            ),
        ]

    mock = Mock(return_value=tool_infos)

    # ----------------------------------------------------------------------
    def GetToolInfos(*args, **kwargs) -> list[ToolInfo.ToolInfo]:
        mock(*args, **kwargs)
        return tool_infos

    # ----------------------------------------------------------------------

    monkeypatch.setattr("dbrownell_ToolsDirectory.ToolInfo.GetToolInfos", GetToolInfos)

    result = CliRunner().invoke(
        __main__.app, ["activate", str(output_filename), output_type, str(tool_directory)] + args
    )
    if expect_failure:
        assert result.exit_code != 0
        return result, None

    assert mock.call_count == 1

    return result, _Args(*mock.mock_calls[0].args, **mock.mock_calls[0].kwargs)


# ----------------------------------------------------------------------
def _ScrubBatchOutput(content: str) -> str:
    id_lookup: dict[str, str] = {}
    guid_lookup: dict[str, str] = {}

    # ----------------------------------------------------------------------
    def IdReplace(match: re.Match) -> str:
        value = match.group("id")

        if value not in id_lookup:
            id_lookup[value] = f"ID_{len(id_lookup) + 1}"

        return id_lookup[value]

    # ----------------------------------------------------------------------
    def GuidReplace(match: re.Match) -> str:
        value = match.group("guid")

        if value not in guid_lookup:
            guid_lookup[value] = f"GUID_{len(guid_lookup) + 1}"

        return guid_lookup[value]

    # ----------------------------------------------------------------------

    content = re.sub(r"id='(?P<id>[0-9]+)'", IdReplace, content)
    content = re.sub("skip_(?P<guid>[0-9a-fA-F]{32})", GuidReplace, content)

    return content


# ----------------------------------------------------------------------
def _ScrubBashOutput(content: str) -> str:
    id_lookup: dict[str, str] = {}

    # ----------------------------------------------------------------------
    def IdReplace(match: re.Match) -> str:
        value = match.group("id")

        if value not in id_lookup:
            id_lookup[value] = f"ID_{len(id_lookup) + 1}"

        return id_lookup[value]

    # ----------------------------------------------------------------------

    content = re.sub(r"id='(?P<id>[0-9]+)'", IdReplace, content)

    return content
