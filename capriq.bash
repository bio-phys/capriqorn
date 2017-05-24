# Bash command completion for capriq.
#
# `source` this file into a bash session (e.g. automatically using .bashrc)
# and use the TAB key to get command suggestions.
#
# This file is part of the Capriqorn package.  See README.rst,
# LICENSE.txt, and the documentation for details.

_capriq()
{
    local cur prev opts \
          example_opts \
          preproc_opts \
          histo_opts \
          postproc_opts  merge_opts unpack_opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="example preproc histo postproc merge unpack --help --version"
    example_opts="--help --expert"
    histo_opts="--help --input"
    preproc_opts=${histo_opts}
    postproc_opts=${histo_opts}
    merge_opts="--help --force --output"
    unpack_opts="--help --force --output"

    if [[ ${prev} == --input ]] ; then
        COMPREPLY=( $(compgen -f -X '!*.yaml' -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == --output ]] ; then
        COMPREPLY=( $(compgen -f -X '!*.yaml' -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == example ]] ; then
        COMPREPLY=( $(compgen -W "${example_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == preproc ]] ; then
        COMPREPLY=( $(compgen -W "${preproc_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == histo ]] ; then
        COMPREPLY=( $(compgen -W "${histo_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == postproc ]] ; then
        COMPREPLY=( $(compgen -W "${postproc_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == merge ]] ; then
        COMPREPLY=( $(compgen -W "${merge_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == unpack ]] ; then
        COMPREPLY=( $(compgen -W "${unpack_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${cur} == * ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _capriq capriq
