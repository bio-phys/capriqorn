#!/bin/bash


if [ "$#" -ne 1 ]; then
    echo 
    echo "Illegal number of parameters"
    echo "File name of pdb file needed to guess aliases!"
    echo 
    exit
fi

PDB_FILE=$1

if [ ! -f $PDB_FILE ]; then
    echo 
    echo "File \"$PDB_FILE\" does not exist!"
    echo 
    exit
fi

awk '/^ATOM/{a=substr($0, 13,4); print a, substr(a,2,1); }' $PDB_FILE  | sort | uniq > alias.initial_guess
echo
echo " Edit \"alias.initial_guess\" by hand (atom names in left column, element names in right column)."
echo 

