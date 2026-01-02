# noqa: D100
import io
import logging
import os
import re

from typing import cast, TYPE_CHECKING

from dbrownell_Common.ContextlibEx import ExitStack
from dotenv import dotenv_values

from dbrownell_ToolsDirectory.Shell.Commands import Augment, Command, EchoOff, Raw, Set

if TYPE_CHECKING:
    from pathlib import Path

    from dbrownell_Common.Streams.DoneManager import DoneManager

    from dbrownell_ToolsDirectory.ToolInfo import ToolInfo


# ----------------------------------------------------------------------
def CreateShellCommands(
    dm: DoneManager,
    tool_infos: list[ToolInfo],
) -> list[Command]:
    r"""Create shell commands to set up the environment for the specified tools.

    For each tool, this function looks for one or more ``.env`` files (as
    determined by :meth:`ToolInfo.GeneratePotentialEnvFiles`) and loads
    environment variables from those files.

    When reading values from a ``.env`` file, any path segment that begins
    with ``./`` or ``.\`` is treated as relative to the directory that
    contains the ``.env`` file itself. The leading ``./`` or ``.\`` is
    replaced with the absolute path to the ``.env`` file's directory plus
    the appropriate path separator.

    Parent-directory references such as ``../`` are not resolved or
    rewritten by this logic; they are left in the value as-is. Only
    current-directory references using ``./`` or ``.\`` are expanded.

    Example:
    * Given an environment file ``/tools/Tool1/Tool1.env`` containing::
          RELATIVE_PATH=./bin
      the value will be expanded to::
          /tools/Tool1/bin

    """

    with dm.Nested("Creating shell commands...") as shell_dm:
        relative_path_re = re.compile(r"(?<!\.)(?P<current_dir>\.[/\\])")

        # ----------------------------------------------------------------------
        def RelativePathReplacement(_: re.Match, env_filename: Path) -> str:
            return str(env_filename.parent) + os.path.sep

        # ----------------------------------------------------------------------

        # Update dotenv's logger to suppress output
        logger_sink = io.StringIO()

        handler = logging.StreamHandler(logger_sink)

        with ExitStack(handler.close):
            logger = logging.getLogger("dotenv.main")

            logger.propagate = False
            logger.setLevel(logging.WARNING)

            logger.handlers.clear()

            logger.addHandler(handler)
            with ExitStack(lambda: logger.removeHandler(handler)):
                # Create the commands
                commands: list[Command] = [EchoOff()]

                for tool_info in tool_infos:
                    commands.append(Augment("PATH", str(tool_info.binary_directory)))

                    # Search for and apply environment files
                    env_config: dict[str, str] = {}

                    for potential_env_file in tool_info.GeneratePotentialEnvFiles():
                        if not potential_env_file.is_file():
                            continue

                        logger_sink.seek(0)
                        logger_sink.truncate(0)

                        # Load the content
                        try:
                            with potential_env_file.open("r", encoding="utf-8") as f:
                                this_env_config = dotenv_values(stream=f)

                            logger_content = logger_sink.getvalue()
                            if logger_content:
                                raise Exception(logger_content.rstrip())  # noqa: TRY301

                        except Exception as ex:
                            shell_dm.WriteError(
                                f"Unable to process the environment file '{potential_env_file}': {ex}\n"
                            )
                            continue

                        # Populate the placeholders
                        for key, value in this_env_config.items():
                            assert value is not None, key

                            this_env_config[key] = relative_path_re.sub(
                                lambda m, potential_env_file=potential_env_file: RelativePathReplacement(
                                    m,
                                    potential_env_file,
                                ),
                                value,
                            )

                        # Commit the results
                        env_config.update(cast(dict[str, str], this_env_config))

                    if env_config:
                        for key, value in env_config.items():
                            commands.append(Set(key, value))

                        commands.append(Raw("\n"))

                return commands
