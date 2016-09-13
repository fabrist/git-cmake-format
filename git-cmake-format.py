#!/usr/bin/python

import argparse
import os
import shlex
import subprocess
import sys


STYLE = '-style=file'
SOURCE_EXTENSIONS = ('.h', '.cpp', '.hpp', '.c', '.cc', '.hh', '.cxx', '.hxx')


def get_git_head():
    rev_parse = subprocess.Popen(
        shlex.split('git rev-parse --verify HEAD'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rev_parse.communicate()
    if rev_parse.returncode:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'


def get_git_root():
    rev_parse = subprocess.Popen(
        shlex.split('git rev-parse --show-toplevel'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rev_parse.stdout.read().strip()


def get_edited_files(in_place):
    head = get_git_head()
    git_args = ['git diff-index']
    if not in_place:
        git_args.append('--cached')
    git_args.extend(['--diff-filter=ACMR --name-only', head])
    git_command = ' '.join(git_args)
    diff_index = subprocess.Popen(shlex.split(git_command),
                                  stdout=subprocess.PIPE)
    diff_index_ret = diff_index.stdout.read().strip()
    diff_index_ret = diff_index_ret.decode()

    return diff_index_ret.split('\n')


def is_formattable(filename, ignore_list):
    for directory in ignore_list:
        if '' != directory and '' != os.path.commonprefix(
                [os.path.relpath(filename), os.path.relpath(directory)]):
            return False
    extension = os.path.splitext(filename)[1]
    return extension in SOURCE_EXTENSIONS


def format_file(clang_format, style, filename, git_root):
    command = ' '.join(
        [clang_format, style, '-i', os.path.join(git_root, filename)])
    subprocess.Popen(shlex.split(command))


def requires_format(clang_format, style, filename):
    git_show_ret = subprocess.Popen(shlex.split('git show:' + filename),
                                    stdout=subprocess.PIPE)
    clang_format_ret = subprocess.Popen(
        shlex.split(''.join([clang_format, style])),
        stdin=git_show_ret.stdout, stdout=subprocess.PIPE)
    formatted_content = clang_format_ret.stdout.read()

    file_content = subprocess.Popen(shlex.split('git show:' + filename),
                                    stdout=subprocess.PIPE).stdout.read()

    return formatted_content != file_content


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    precommit_parser = subparsers.add_parser('pre-commit')
    precommit_parser.set_defaults(in_place=False)
    cmake_parser = subparsers.add_parser('cmake')
    cmake_parser.set_defaults(in_place=True)
    parser.add_argument('clang_format_path', metavar='clang-format-path')

    args = parser.parse_args()
    return_code = 0
    ignore_list = ()
    edited_files = get_edited_files(args.in_place)

    if args.in_place:
        git_root = get_git_root()
        for filename in edited_files:
            if is_formattable(filename, ignore_list):
                format_file(args.clang_format_path, STYLE, filename, git_root)
    else:
        unformatted = [
            filename for filename in edited_files
            if is_formattable(filename, ignore_list) and
            requires_format(args.clang_format_path, STYLE, filename)]
        if unformatted:
            print ('The following files must be formatted. '
                   'Please run "make format":\n' + '\n'.join(unformatted))
            return_code = 1

    if return_code:
        subprocess.Popen(shlex.split('git reset HEAD -- .'))

    sys.exit(return_code)
