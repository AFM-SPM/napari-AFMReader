# Repository Guidelines

## Project Structure & Module Organization

This is a Python napari plugin for AFMReader. Runtime code lives in `src/napari_afmreader/`, with plugin metadata in `src/napari_afmreader/napari.yaml`. Tests are colocated under `src/napari_afmreader/_tests/`; test fixtures and sample data are in `_tests/_test_data/`. User-facing plugin guidance is maintained in `README.md`.

## Build, Test, and Development Commands

These commands should only be run when specifcally requested. Do not try and run the test suite unless we are working on tests, the tests are a bit bad for this project and hence do little to help with development

```bash
pre-commit run --all-files
```

Launch napari locally with:

```bash
napari
```

This opens a gui app and can be used to test the application through the computer use tool (this is generally prefereable to running the test suite) however again this should not be done unless requested.

Do not try and add commit or push requests unless specifically requested. If the code you have written has been changed when you got to edit it over what you were familiar with do not revert it, it has been changed for a reason.
If you think reverting the change is the best solution, you absolutely **must** stop and ask me before making any of those changes

## Coding Style & Naming Conventions

Code is formatted with Black using a 120-character line length. Ruff handles import ordering and lint fixes; Pylint is also run through pre-commit. Use 4-space indentation, clear snake_case names for functions and variables, and CapWords for classes. Keep internal modules consistent with the existing leading-underscore pattern, such as `_reader.py`. Tests should follow the `test_*.py` naming pattern enforced by pre-commit.

## Configuration & Assets

Keep package data paths under `src/napari_afmreader/` so they are included by the plugin package.
