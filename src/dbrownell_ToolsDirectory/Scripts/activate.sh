#!/usr/bin/env bash

set +v
set +x

output_color=[33m[1m
success_color=[32m[1m
error_color=[31m[1m

echo "${output_color}"
echo "                              ---------------------------"
echo "============================== L O A D I N G   T O O L S =============================="
echo "                              ---------------------------"
echo ""
echo "               https://github.com/davidbrownell/dbrownell_ToolsDirectory"
echo "[0m"

# Push the current directory
this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pushd "${this_dir}" > /dev/null

function Execute() {
    # Ensure that we are running in Bash
    if [[ "${BASH_VERSINFO}" == "" ]]; then
        echo ""
        echo "${error_color}ERROR:[0m Activation is only supported within a bash shell."
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m     [\${BASH_VERSINFO} is not defined]"
        echo "${error_color}ERROR:[0m"
        echo ""

        return 1
    fi

    # Ensure that the script is being invoked via source (as it modifies the current environment)
    if [[ ${0##*/} == activate.sh ]]; then
        echo ""
        echo "${error_color}ERROR:[0m Because this process makes changes to environment variables, it must be run within the current context."
        echo "${error_color}ERROR:[0m To do this, please source (run) the script as follows:"
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m     source activate.sh"
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m         - or -"
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m     . activate.sh"
        echo "${error_color}ERROR:[0m"
        echo ""

        return 1
    fi

    # Create a temporary file that contains the output produced by dbrownell_ToolsDirectory.
    if [[ ${OSTYPE} == *darwin* ]]; then
        temp_filename=$(mktemp -t TempFile.XXXXXX)
    else
        temp_filename=$(mktemp)
    fi

    echo "${output_color}"
    echo "Creating dynamic commands..."
    echo "[0m"

    uv run python -m dbrownell_ToolsDirectory "${temp_filename}" bash "$@"
    script_generation_return_code=$?

    # Invoke the script
    if [[ -e ${temp_filename} ]]; then
        echo "${output_color}"
        echo "Running dynamic commands..."
        echo "[0m"

        chmod u+x "${temp_filename}"
        source "${temp_filename}"
    fi
    script_execution_return_code=$?

    # Process errors
    if [[ ${script_generation_return_code} -ne 0 ]]; then
        echo ""
        echo "${error_color}ERROR:[0m Errors were encountered and the tool directories have not been activated."
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m     [dbrownell_ToolsDirectory failed]"
        echo "${error_color}ERROR:[0m"
        echo ""

        return 1
    fi

    if [[ ${script_execution_return_code} -ne 0 ]]; then
        echo ""
        echo "${error_color}ERROR:[0m Errors were encountered and the tool directories have not been activated."
        echo "${error_color}ERROR:[0m"
        echo "${error_color}ERROR:[0m     [${temp_filename} failed]"
        echo "${error_color}ERROR:[0m"
        echo ""

        return 1
    fi

    rm -f "${temp_filename}"

    echo "${success_color}SUCCESS:[0m Tool directories have been activated."
    echo ""

    echo "${output_color}"
    echo ""
    echo "======================================================================================="
    echo "[0m"

    return 0
}

Execute "$@"

popd > /dev/null
