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
          preproc_opts preproc_example_opts \
          histo_opts histo_example_opts \
          postproc_opts postproc_example_opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    opts="preproc preproc-example histo histo-example postproc postproc-example -h --help"
    histo_opts="-h --help --input"
    histo_example_opts="-h --help --output"
    preproc_opts=${histo_opts}
    preproc_example_opts=${histo_example_opts}
    postproc_opts=${histo_opts}
    postproc_example_opts=${histo_example_opts}

    if [[ ${prev} == --input ]] ; then
        COMPREPLY=( $(compgen -f -X '!*.yaml' -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == --output ]] ; then
        COMPREPLY=( $(compgen -f -X '!*.yaml' -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == preproc ]] ; then
        COMPREPLY=( $(compgen -W "${preproc_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == preproc-example ]] ; then
        COMPREPLY=( $(compgen -W "${preproc_example_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == histo ]] ; then
        COMPREPLY=( $(compgen -W "${histo_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == histo-example ]] ; then
        COMPREPLY=( $(compgen -W "${histo_example_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == postproc ]] ; then
        COMPREPLY=( $(compgen -W "${postproc_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${prev} == postproc-example ]] ; then
        COMPREPLY=( $(compgen -W "${postproc_example_opts}" -- ${cur}) )
        return 0
    fi
    if [[ ${cur} == * ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _capriq capriq
