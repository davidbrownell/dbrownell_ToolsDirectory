@echo off

set _DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR=[33m[1m
set _DBROWNELL_TOOLS_DIRECTORY_SUCCESS_COLOR=[32m[1m
set _DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR=[31m[1m

@echo %_DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR%
@echo                               ---------------------------
@echo ============================== L O A D I N G   T O O L S ==============================
@echo                               ---------------------------
@echo.
@echo                https://github.com/davidbrownell/dbrownell_ToolsDirectory
@echo [0m

pushd %~dp0

REM Create a temporary file that contains the output produced by dbrownell_ToolsDirectory.
call :CreateTempScriptName

@echo %_DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR%
@echo Creating dynamic commands...
@echo [0m

uv run python -m dbrownell_ToolsDirectory activate "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%" batch %*
set _DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE=%ERRORLEVEL%

REM Invoke the script
if exist "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%" (
    @echo %_DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR%
    @echo.
    @echo Running dynamic commands...
    @echo [0m

    call "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%"
)
set _DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE=%ERRORLEVEL%

REM Process errors
if "%_DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE%" NEQ "0" (
    @echo.
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m Errors were encountered and the tool directories have not been activated.
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m     [dbrownell_ToolsDirectory failed]
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m

    goto ErrorExit
)

if "%_DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE%" NEQ "0" (
    @echo.
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m Errors were encountered and the tool directories have not been activated.
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m     [%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME% failed]
    @echo %_DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR%ERROR:[0m
    @echo.

    goto ErrorExit
)

REM Success
del "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%"

@echo %_DBROWNELL_TOOLS_DIRECTORY_SUCCESS_COLOR%SUCCESS:[0m The tool directories have been activated.
@echo.

@echo %_DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR%
@echo.
@echo =======================================================================================
@echo [0m

@REM ----------------------------------------------------------------------
set _DBROWNELL_TOOLS_DIRECTORY_RETURN_CODE=0
goto Exit

@REM ----------------------------------------------------------------------
:ErrorExit

set _DBROWNELL_TOOLS_DIRECTORY_RETURN_CODE=-1
goto Exit

@REM ----------------------------------------------------------------------
:Exit
set _DBROWNELL_TOOLS_DIRECTORY_OUTPUT_COLOR=
set _DBROWNELL_TOOLS_DIRECTORY_SUCCESS_COLOR=
set _DBROWNELL_TOOLS_DIRECTORY_ERROR_COLOR=
set _DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME=
set _DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE=
set _DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE=

popd

exit /B %_DBROWNELL_TOOLS_DIRECTORY_RETURN_CODE%

@REM ----------------------------------------------------------------------
@REM |
@REM |  Internal Functions
@REM |
@REM ----------------------------------------------------------------------
:CreateTempScriptName
setlocal EnableDelayedExpansion
set _filename=%CD%\ExecuteImpl-!RANDOM!-!Time:~6,5!.cmd
endlocal & set _DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME=%_filename%

if exist "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%" goto CreateTempScriptName
goto :EOF
