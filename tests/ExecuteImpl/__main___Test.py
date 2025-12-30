from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

from click.testing import Result
from dbrownell_Common.Streams.DoneManager import DoneManager
from pyfakefs.fake_filesystem import FakeFilesystem
from _pytest.monkeypatch import MonkeyPatch
from semantic_version import Version as SemVer
from typer.testing import CliRunner

from dbrownell_ToolsDirectory import ToolInfo
from dbrownell_ToolsDirectory.ExecuteImpl import __main__


# ----------------------------------------------------------------------
def test_NoArgs(fs, monkeypatch):
    execute_result = _Execute(fs, monkeypatch, [])
    assert isinstance(execute_result, tuple)

    result = execute_result[0]
    args = execute_result[1]

    assert result.exit_code == 0

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
    execute_result = _Execute(fs, monkeypatch, ["--include", "A", "--include", "B", "--exclude", "C"])
    assert isinstance(execute_result, tuple)

    result = execute_result[0]
    args = execute_result[1]

    assert result.exit_code == 0

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
    execute_result = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "ToolA=1.2.3", "--tool-version", "ToolB=4.5.6"],
    )

    assert isinstance(execute_result, tuple)

    result = execute_result[0]
    args = execute_result[1]

    assert result.exit_code == 0

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
    result = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "InvalidToolVersionString"],
        expect_failure=True,
    )

    assert isinstance(result, Result)

    assert result.exit_code != 0


# ----------------------------------------------------------------------
def test_InvalidToolVersionValue(fs, monkeypatch):
    result = _Execute(
        fs,
        monkeypatch,
        ["--tool-version", "ToolA=NotASemVer"],
        expect_failure=True,
    )

    assert isinstance(result, Result)

    assert result.exit_code != 0


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
    tool_directory: Path = Path("does/not/exist"),
    output_filename: Path = Path("output.file"),
    output_type: str = "bash",
    *,
    expect_failure: bool = False,
) -> tuple[Result, _Args] | Result:
    fs.create_file(tool_directory / "dummy.txt")

    mock = Mock(return_value=[])

    monkeypatch.setattr("dbrownell_ToolsDirectory.ToolInfo.GetToolInfos", mock)

    result = CliRunner().invoke(__main__.app, [str(tool_directory), str(output_filename), output_type] + args)
    if expect_failure:
        assert result.exit_code != 0
        return result

    assert mock.call_count == 1

    return result, _Args(*mock.mock_calls[0].args, **mock.mock_calls[0].kwargs)
