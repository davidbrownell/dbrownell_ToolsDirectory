@echo off

REM Create a temporary file that contains the output produced by dbrownell_ToolsDirectory.
call :CreateTempScriptName

uv run python -m dbrownell_ToolsDirectory "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%" batch %*
set _DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE=%ERRORLEVEL%

REM Invoke the script
if exist "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%" (
    call "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%"
)
set _DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE=%ERRORLEVEL%

REM Process errors
if "%_DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE%" NEQ "0" (
    @echo.
    @echo [31m[1mERROR:[0m Errors were encountered and the tool directories have not been activated.
    @echo [31m[1mERROR:[0m
    @echo [31m[1mERROR:[0m     [dbrownell_ToolsDirectory failed]
    @echo [31m[1mERROR:[0m

    goto ErrorExit
)

if "%_DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE%" NEQ "0" (
    @echo.
    @echo [31m[1mERROR:[0m Errors were encountered and the tool directories have not been activated.
    @echo [31m[1mERROR:[0m
    @echo [31m[1mERROR:[0m     [%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME% failed]
    @echo [31m[1mERROR:[0m
    @echo.

    goto ErrorExit
)

REM Success
del "%_DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME%"

@echo.
@echo [32m[1mSUCCESS:[0m The tool directories have been activated.
@echo.
@echo.

@REM ----------------------------------------------------------------------
set _DBROWNELL_TOOLS_DIRECTORY_RETURN_CODE=0
goto Exit

@REM ----------------------------------------------------------------------
:ErrorExit

set _DBROWNELL_TOOLS_DIRECTORY_RETURN_CODE=-1
goto Exit

@REM ----------------------------------------------------------------------
:Exit
set _DBROWNELL_TOOLS_DIRECTORY_TEMP_SCRIPT_NAME=
set _DBROWNELL_TOOLS_SCRIPT_GENERATION_RETURN_CODE=
set _DBROWNELL_TOOLS_SCRIPT_EXECUTION_RETURN_CODE=

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
