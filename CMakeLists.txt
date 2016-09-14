cmake_minimum_required(VERSION 2.8)
project(git-clang-format-cmake NONE)

set(CLANG_FORMAT_BASENAME "clang-format-3.4")
find_program(CLANG_FORMAT ${CLANG_FORMAT_BASENAME})
if(CLANG_FORMAT)
    message(STATUS "Found: '${CLANG_FORMAT_BASENAME}'")
else()
    message(FATAL_ERROR "Could not find '${CLANG_FORMAT_BASENAME}'")
endif()

set(GCF_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/git-cmake-format.py)

execute_process(COMMAND git rev-parse --show-toplevel
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/..
    OUTPUT_VARIABLE GCF_GIT_ROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT GCF_GIT_ROOT)
    message(FATAL_ERROR "Not in a git repository")
else()
    message(STATUS "Found git root: ${GCF_GIT_ROOT}")
endif()
set(PRECOMMIT_FILE  ${GCF_GIT_ROOT}/.git/hooks/pre-commit)

set(HOOK_COMMAND
    "${PYTHON_EXECUTABLE} ${GCF_SCRIPT} pre-commit ${CLANG_FORMAT}")
if(EXISTS ${PRECOMMIT_FILE})
    file(READ ${PRECOMMIT_FILE} ORIGINAL_PRECOMMIT_HOOK)
    string(FIND ${ORIGINAL_PRECOMMIT_HOOK} ${HOOK_COMMAND} HOOK_OFFSET)
    if(HOOK_OFFSET EQUAL -1)
        file(APPEND ${PRECOMMIT_FILE} "\n${HOOK_COMMAND}")
    endif()
else()
    file(WRITE ${PRECOMMIT_FILE} "#!/bin/bash\n\n${HOOK_COMMAND}")
endif()

add_custom_target(format
    ${PYTHON_EXECUTABLE} ${GCF_SCRIPT} cmake ${CLANG_FORMAT}
	WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
