# General

# Python

- All function names must be PascalCase.

- Always introduce a single blank line between a function's docstring and the first statement in the function. Docstrings should not contain information about arguments, as the argument names should be descriptive enough to communicate how they are used in the function and when the function is invoked.

- All function and class definitions must be prefixed with "# ----------------------------------------------------------------------".

- Code should be organized by public types, public functions, private types, and private functions. Do not mix public and private types and functions. Class types and methods should be organized in the same way.

- Use textwrap.dedent when writing multiline strings.

# uv

- When adding new package dependencies, don't add them directly to pyproject.toml but rather add them through the command line via "uv add <package_name>". This ensures that the latest package will be installed, rather than the package version most commonly encountered during model training.

# Project
