#!/usr/bin/python

import os
import subprocess
import sys


GIT = 'git'
CLANG_FORMAT = 'clang-format'  # TODO
STYLE = '-style=file'
ignore_list = []


def get_git_head():
    rev_parse = subprocess.Popen(
        [GIT, 'rev-parse', '--verify', 'HEAD'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rev_parse.communicate()
    if rev_parse.returncode:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'


def get_git_root():
    rev_parse = subprocess.Popen(
        [GIT, 'rev-parse', '--show-toplevel'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rev_parse.stdout.read().strip()


def get_edited_files(in_place):
    head = get_git_head()
    git_args = [GIT, 'diff-index']
    if not in_place:
        git_args.append('--cached')
    git_args.extend(['--diff-filter=ACMR', '--name-only', head])
    diff_index = subprocess.Popen(git_args, stdout=subprocess.PIPE)
    diff_index_ret = diff_index.stdout.read().strip()
    diff_index_ret = diff_index_ret.decode()

    return diff_index_ret.split('\n')


def is_formattable(filename):
    for directory in ignore_list:
        if '' != directory and '' != os.path.commonprefix(
                [os.path.relpath(filename), os.path.relpath(directory)]):
            return False
    extension = os.path.splitext(filename)[1]
    for ext in ['.h', '.cpp', '.hpp', '.c', '.cc', '.hh', '.cxx', '.hxx']:
        if ext == extension:
            return True
    return False


def format_file(filename, git_root):
    subprocess.Popen(
        [CLANG_FORMAT, STYLE, '-i', os.path.join(git_root, filename)])
    return


def requires_format(filename):
    git_show_ret = subprocess.Popen([GIT, "show", ":" + filename],
                                    stdout=subprocess.PIPE)
    clang_format_ret = subprocess.Popen([CLANG_FORMAT, STYLE],
                                        stdin=git_show_ret.stdout,
                                        stdout=subprocess.PIPE)
    formatted_content = clang_format_ret.stdout.read()

    file_content = subprocess.Popen([GIT, "show", ":" + filename],
                                    stdout=subprocess.PIPE).stdout.read()

    if formatted_content == file_content:
        return False
    return True


def print_usage_and_exit():
    print ("Usage: " + sys.argv[0] + " [--pre-commit|--cmake] " +
           "[<path/to/git>] [<path/to/clang-format]")
    sys.exit(1)


if __name__ == "__main__":
    if 2 > len(sys.argv):
        print_usage_and_exit()

    if "--pre-commit" == sys.argv[1]:
        in_place = False
    elif "--cmake" == sys.argv[1]:
        in_place = True
    else:
        print_usage_and_exit()

    for arg in sys.argv[2:]:
        if "git" in arg:
            GIT = arg
        elif "clang-format" in arg:
            CLANG_FORMAT = arg
        elif "-style=" in arg:
            STYLE = arg
        elif "-ignore=" in arg:
            ignore_list = arg.strip("-ignore=").split(";")
        else:
            print_usage_and_exit()

    edited_files = get_edited_files(in_place)

    return_code = 0

    if in_place:
        git_root = get_git_root()
        for filename in edited_files:
            if is_formattable(filename):
                format_file(filename, git_root)
        sys.exit(return_code)

    for filename in edited_files:
        if not is_formattable(filename):
            continue
        if requires_format(filename):
            print ("'" + filename +
                   "' must be formatted, run the cmake target 'format'")
            return_code = 1

    if 1 == return_code:
        subprocess.Popen([GIT, "reset", "HEAD", "--", "."])

    sys.exit(return_code)
