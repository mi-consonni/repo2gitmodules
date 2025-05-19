#!/usr/bin/env python3

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys


def main():
    try:
        args = parse_args()
        run_app(args)
    except Exception as e:
        log_error(f'Error: {e}')
        sys.exit(1)
    finally:
        if os.path.exists('.repo'):
            shutil.rmtree('.repo')


def parse_args():
    parser = argparse.ArgumentParser(description='Convert repo manifest to git submodules')
    parser.add_argument('-u', '--manifest-url', required=True, help='Manifest repository URL')
    parser.add_argument('-b', '--branch', required=False, default='main', help='Manifest branch')
    parser.add_argument('-m', '--manifest', required=False,
                        default='default.xml', help='Manifest file name')
    return parser.parse_args()


def run_app(args):
    root_dir = os.getcwd()
    ensure_git_dir(root_dir)
    manifest = extract_repo_manifest(root_dir, args)
    sync_git_submodules(root_dir, manifest)


def ensure_git_dir(root_dir):
    git_dir = os.path.join(root_dir, '.git')
    if not os.path.exists(git_dir):
        run_git_subprocess(['init'])
    else:
        if not is_git_clean():
            raise RuntimeError('Git repository is not clean. Please commit or stash your changes.')


def is_git_clean():
    try:
        run_git_subprocess(['diff-index', '--exit-code', 'HEAD'], hide_stderr=True)
        return True
    except subprocess.CalledProcessError:
        return False


def extract_repo_manifest(root_dir, args):
    log_trace('Retrieving repo manifest...')
    run_repo_init(args)
    repo_dir = os.path.join(root_dir, '.repo')
    import_dyn_manifest_xml(repo_dir)
    manifest_path = os.path.join(repo_dir, 'manifest.xml')
    return manifest_xml.XmlManifest(repo_dir, manifest_path)


def run_repo_init(args):
    run_subprocess(['repo', 'init',
                    '-u', args.manifest_url,
                    '-b', args.branch,
                    '-m', args.manifest])


def import_dyn_manifest_xml(repo_dir):
    global manifest_xml
    repo_module_dir = os.path.join(repo_dir, 'repo')
    module_name = 'manifest_xml'
    file_path = os.path.join(repo_module_dir, module_name + '.py')
    sys.path.insert(0, repo_module_dir)
    manifest_xml = import_dyn_module(module_name, file_path)


def import_dyn_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sync_git_submodules(root_dir, manifest):
    # Remove submodules not in manifest.
    current_submodules = get_git_submodules()
    manifest_paths = set(os.path.relpath(p.worktree, root_dir) for p in manifest.projects)
    for submodule in current_submodules:
        if submodule not in manifest_paths:
            remove_git_submodule(submodule)
    # Add or update submodules from manifest.
    for project in manifest.projects:
        sync_git_submodule(root_dir, project)


def get_git_submodules():
    result = run_git_subprocess(['submodule', 'status'])
    submodules = []
    for line in result.splitlines():
        _, path, _ = line.split()
        submodules.append(path)
    return submodules


def remove_git_submodule(worktree):
    log_trace(f'Removing submodule {worktree}...')
    run_git_subprocess(['submodule', 'deinit', worktree])
    # Remove the submodule from the working tree.
    run_git_subprocess(['rm', worktree])
    # Remove the submodule from .git/modules.
    shutil.rmtree(os.path.join('.git', 'modules', worktree), ignore_errors=True)


def sync_git_submodule(root_dir, project):
    worktree = os.path.relpath(project.worktree, root_dir)
    revision = project.revisionId if project.revisionId is not None else project.revisionExpr
    if is_git_submodule_exists(worktree):
        log_trace(f'Updating submodule {worktree}...')
        update_git_submodule(worktree, project.remote.url, project.upstream)
    else:
        log_trace(f'Adding submodule {worktree}...')
        add_git_submodule(worktree, project.remote.url, project.upstream)
    log_trace(f'Checking out {worktree} to {revision}...')
    checkout_git_submodule(worktree, revision)


def is_git_submodule_exists(worktree):
    try:
        run_git_subprocess(['submodule', 'status', worktree], hide_stderr=True)
        return True
    except subprocess.CalledProcessError:
        return False


def update_git_submodule(worktree, url, branch=None):
    run_git_subprocess(['submodule', 'set-url', worktree, url])
    # When removing the branch to a submodule that does not have a branch,
    # the command fails, so we need to add a dummy branch first.
    run_git_subprocess(['submodule', 'set-branch', '--branch', 'dummy', worktree])
    branch_opt = ['--default'] if branch is None else ['--branch', branch]
    run_git_subprocess(['submodule', 'set-branch'] + branch_opt + [worktree])
    run_git_subprocess(['-C', worktree, 'fetch', '--all'])


def add_git_submodule(worktree, url, branch=None):
    branch_opt = [] if branch is None else ['-b', branch]
    run_git_subprocess(['submodule', 'add'] + branch_opt + [url, worktree])


def checkout_git_submodule(worktree, revision):
    run_git_subprocess(['-C', worktree, 'checkout', revision])
    run_git_subprocess(['add', worktree])
    # Recursively update its submodules.
    run_git_subprocess(['submodule', 'update', '--init', '--recursive', worktree])


def run_git_subprocess(args, hide_stderr=False):
    return run_subprocess(['git'] + args, hide_stderr=hide_stderr)


def run_subprocess(args, hide_stderr=False):
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        if not hide_stderr:
            log_error(f'Command `{" ".join(args)}` failed: {e.stderr}')
        raise e
    return result.stdout


def log_trace(msg):
    print(msg)


def log_error(msg):
    print(msg, file=sys.stderr)


if __name__ == '__main__':
    main()
