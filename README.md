# doc2quiz

This project is used to generate quiz questions from a pdf document.


## Project Organization

https://github.com/microsoft/python-package-template was used to setup the
project.

to run the program under bin/, you might have to add the src dir to your
python path with:

python3.10 -m pip install -e .



- `bin`: doc2quiz executable
- `src`: main source code doc doc2quiz
- `.github/workflows`: Contains GitHub Actions used for building, testing, and publishing.
- `.devcontainer/Dockerfile`: Contains Dockerfile to build a development container for VSCode 
- `.devcontainer/devcontainer.json`: Contains the configuration for the development container for VSCode, including the Docker image to use, any additional VSCode extensions to install, and whether or not to mount the project directory into the container.
- `.vscode/settings.json`: Contains VSCode settings specific to the project, such as the Python interpreter to use and the maximum line length for auto-formatting.
- `tests`: Contains Python-based test cases to validate source code.
- `pyproject.toml`: Contains metadata about the project and configurations for additional tools used to format, lint, type-check, and analyze Python code.



