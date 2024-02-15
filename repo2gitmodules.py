#!/usr/bin/env python3

import importlib.util
import os
import shutil
import subprocess
import sys


def import_dyn_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def import_dyn_manifest_xml(repo_dir):
    global manifest_xml
    repo_module_dir = os.path.join(repo_dir, 'repo')
    module_name = 'manifest_xml'
    file_path = os.path.join(repo_module_dir, module_name + '.py')
    sys.path.insert(0, repo_module_dir)
    manifest_xml = import_dyn_module(module_name, file_path)


def load_manifest(repo_dir, manifest_file='manifest.xml'):
    manifest_path = os.path.join(repo_dir, manifest_file)
    return manifest_xml.XmlManifest(repo_dir, manifest_path)


def run_git_subprocess(args):
    subprocess.run(['git'] + args, check=True)


def run_git_init():
    run_git_subprocess(['init'])


def run_git_submodule_add(worktree, url, branch=None):
    branch_opt = [] if branch is None else ['-b', f'{branch}']
    run_git_subprocess(['submodule', 'add'] +
                       branch_opt + [f'{url}', f'{worktree}'])


def run_git_submodule_checkout(worktree, revision):
    run_git_subprocess(['-C', f'{worktree}', 'checkout', f'{revision}'])


def add_gitmodule(project):
    worktree = os.path.relpath(project.worktree, os.getcwd())
    revision = project.revisionId if project.revisionId is not None else project.revisionExpr
    run_git_submodule_add(worktree, project.remote.url, project.upstream)
    run_git_submodule_checkout(worktree, revision)


def add_gitmodules(manifest):
    run_git_init()
    for project in manifest.projects:
        add_gitmodule(project)


def main():
    # TODO: Sanity checks: directory exists, is a repo dir, is a git dir, ...
    repo_dir = os.path.join(os.getcwd(), '.repo')
    import_dyn_manifest_xml(repo_dir)
    manifest = load_manifest(repo_dir)
    add_gitmodules(manifest)
    shutil.rmtree(repo_dir)


if __name__ == '__main__':
    main()
