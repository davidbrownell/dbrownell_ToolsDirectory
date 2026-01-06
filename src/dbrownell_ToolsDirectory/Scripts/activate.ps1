#Requires -Version 5.1

param()

# Set colors
$outputColor = [ConsoleColor]::Yellow
$successColor = [ConsoleColor]::Green
$errorColor = [ConsoleColor]::Red

# Display loading message
Write-Host -ForegroundColor $outputColor @"
                              ---------------------------
============================== L O A D I N G   T O O L S ==============================
                              ---------------------------

               https://github.com/davidbrownell/dbrownell_ToolsDirectory

"@

# Push the current directory
Push-Location $PSScriptRoot

try {
    # Ensure that we are running in PowerShell
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        Write-Host -ForegroundColor $errorColor @"

ERROR: Activation is only supported in PowerShell 5.1 or later.
ERROR:
ERROR:     [PowerShell version $($PSVersionTable.PSVersion) is not supported]
ERROR:

"@

        exit 1
    }

    # Ensure that the script is being invoked via dot-sourcing (as it modifies the current environment)
    if ($MyInvocation.CommandOrigin -eq 'Runspace') {
        Write-Host -ForegroundColor $errorColor @"

ERROR: Because this process makes changes to environment variables, it must be run within the current context.
ERROR: To do this, please dot-source (run) the script as follows:
ERROR:
ERROR:     . .\activate.ps1
ERROR:

"@

        exit 1
    }

    # Create a temporary file that contains the output produced by dbrownell_ToolsDirectory.
    $tempFileName = [System.IO.Path]::GetTempFileName() + ".ps1"

    Write-Host ""
    Write-Host -ForegroundColor $outputColor @"
Creating dynamic commands...

"@

    & uv run python -m dbrownell_ToolsDirectory $tempFileName powershell $args
    $scriptGenerationReturnCode = $LASTEXITCODE

    # Invoke the script
    if (Test-Path $tempFileName) {
        Write-Host -ForegroundColor $outputColor @"

Running dynamic commands...

"@

        . $tempFileName
        $scriptExecutionReturnCode = $LASTEXITCODE
    } else {
        $scriptExecutionReturnCode = 0
    }

    # Process errors
    if ($scriptGenerationReturnCode -ne 0) {
        Write-Host -ForegroundColor $errorColor @"

ERROR: Errors were encountered and the tool directories have not been activated.
ERROR:
ERROR:     [dbrownell_ToolsDirectory failed]
ERROR:

"@

        exit 1
    }

    if ($scriptExecutionReturnCode -ne 0) {
        Write-Host -ForegroundColor $errorColor @"

ERROR: Errors were encountered and the tool directories have not been activated.
ERROR:
ERROR:     [$tempFileName failed]
ERROR:

"@

        exit 1
    }

    # Clean up
    if (Test-Path $tempFileName) {
        Remove-Item $tempFileName -Force
    }

    Write-Host -ForegroundColor $successColor "SUCCESS: Tool directories have been activated."
    Write-Host ""

    Write-Host -ForegroundColor $outputColor @"


=======================================================================================

"@

} finally {
    Pop-Location
}
