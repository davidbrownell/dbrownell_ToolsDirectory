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
from dbrownell_ToolsDirectory import ManifestGenerator


# ----------------------------------------------------------------------
def test_NoArgs(fs, monkeypatch):
    result, args = _Execute(fs, monkeypatch, [])

    assert result.exit_code == 0

    assert args is not None
    assert args.tool_directory
    assert args.include_tools == set()
    assert args.exclude_tools == set()
    assert args.tool_versions == dict()
    assert args.allow_generic_operating_systems is True
    assert args.allow_generic_architectures is True
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
    assert args.allow_generic_operating_systems is True
    assert args.allow_generic_architectures is True
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
    assert args.allow_generic_operating_systems is True
    assert args.allow_generic_architectures is True
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
def test_Manifest(fs: FakeFilesystem, monkeypatch: MonkeyPatch):
    result, args = _ExecuteManifest(fs, monkeypatch, ["--yes"])

    assert result.exit_code == 0

    assert args is not None
    assert args.tool_directory
    assert args.include_tools is None
    assert args.exclude_tools is None


# ----------------------------------------------------------------------
def test_ManifestWithIncludeExclude(fs: FakeFilesystem, monkeypatch: MonkeyPatch):
    result, args = _ExecuteManifest(
        fs,
        monkeypatch,
        ["--include", "ToolA", "--include", "ToolB", "--exclude", "ToolC", "--yes"],
    )

    assert result.exit_code == 0

    assert args is not None
    assert args.include_tools == {"ToolA", "ToolB"}
    assert args.exclude_tools == {"ToolC"}


# ----------------------------------------------------------------------
def test_ManifestConfirmationAccepted(fs: FakeFilesystem, monkeypatch: MonkeyPatch):
    # Mock the interactive mode check to return True
    monkeypatch.setattr("dbrownell_ToolsDirectory.__main__._IsInteractiveMode", lambda: True)

    result, args = _ExecuteManifest(fs, monkeypatch, [], input="y\n")

    assert result.exit_code == 0
    assert (
        textwrap.dedent(
            """\

            WARNING: The manifest will contain the full contents of .env files, which may
            include passwords, API keys, or other sensitive information. These values will
            be written to the output file in plain text.

            """,
        )
        in result.output
    )
    assert args is not None


# ----------------------------------------------------------------------
def test_ManifestConfirmationDeclined(fs: FakeFilesystem, monkeypatch: MonkeyPatch):
    # Mock the interactive mode check to return True
    monkeypatch.setattr("dbrownell_ToolsDirectory.__main__._IsInteractiveMode", lambda: True)

    result, _ = _ExecuteManifest(fs, monkeypatch, [], input="n\n")

    assert result.exit_code == 1
    assert (
        textwrap.dedent(
            """\

            WARNING: The manifest will contain the full contents of .env files, which may
            include passwords, API keys, or other sensitive information. These values will
            be written to the output file in plain text.

            """,
        )
        in result.output
    )


# ----------------------------------------------------------------------
def test_ManifestNonInteractiveWithoutYes(fs: FakeFilesystem, monkeypatch: MonkeyPatch):
    # Mock the interactive mode check to return False (non-interactive)
    monkeypatch.setattr("dbrownell_ToolsDirectory.__main__._IsInteractiveMode", lambda: False)

    result, _ = _ExecuteManifest(fs, monkeypatch, [])

    assert result.exit_code == 1
    assert result.output == "ERROR: The --yes flag is required when running in non-interactive mode.\n"


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
    allow_generic_operating_systems: bool
    allow_generic_architectures: bool


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class _ManifestArgs:
    dm: DoneManager
    tool_directory: Path
    include_tools: set[str] | None
    exclude_tools: set[str] | None


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
    def GetAllToolInfos(*args, **kwargs) -> list[ToolInfo.ToolInfo]:
        mock(*args, **kwargs)
        return tool_infos

    # ----------------------------------------------------------------------

    monkeypatch.setattr("dbrownell_ToolsDirectory.ToolInfo.GetAllToolInfos", GetAllToolInfos)

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


# ----------------------------------------------------------------------
def _ExecuteManifest(
    fs: FakeFilesystem,
    monkeypatch: MonkeyPatch,
    args: list[str],
    tool_directory: Path = Path("tools"),
    output_filename: Path = Path("manifest.yaml"),
    input: str | None = None,
) -> tuple[Result, _ManifestArgs | None]:
    fs.create_dir(tool_directory)

    manifest = ManifestGenerator.ToolsManifest(tools=[])

    generate_mock = Mock(return_value=manifest)
    write_mock = Mock()

    # ----------------------------------------------------------------------
    def MockGenerateManifest(*args, **kwargs) -> ManifestGenerator.ToolsManifest:
        generate_mock(*args, **kwargs)
        return manifest

    # ----------------------------------------------------------------------
    def MockWriteManifestYaml(*args, **kwargs) -> None:
        write_mock(*args, **kwargs)

    # ----------------------------------------------------------------------

    monkeypatch.setattr("dbrownell_ToolsDirectory.__main__.GenerateManifest", MockGenerateManifest)
    monkeypatch.setattr("dbrownell_ToolsDirectory.__main__.WriteManifestYaml", MockWriteManifestYaml)

    result = CliRunner().invoke(
        __main__.app,
        ["manifest", str(tool_directory), str(output_filename)] + args,
        input=input,
    )

    if result.exit_code != 0:
        return result, None

    assert generate_mock.call_count == 1
    assert write_mock.call_count == 1

    return result, _ManifestArgs(*generate_mock.mock_calls[0].args, **generate_mock.mock_calls[0].kwargs)
