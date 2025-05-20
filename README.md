repo2gitmodules
===============

A simple Python script to import all repositories listed in a [`repo`](https://source.android.com/docs/setup/reference/repo) manifest as `git` submodules.

Both `repo` and `git` commands must be already installed.

Note: we prefer to spawn subprocesses instead of depending on external libraries to allow direct usage of the script without any additional setup.
