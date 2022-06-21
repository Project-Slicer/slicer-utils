#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: $0 <pp> <checkpoint_dir>"
  exit 1
fi

pp="$1 -s --fuzzy-strace"
checkpoint_dir=$2

function run() {
  echo "Running $1" 1>&2
  $pp $1
  ret=$?
  if [ $ret -ne 0 ]; then
    echo "error, return code $ret" 1>&2
  fi
}

for f in $checkpoint_dir/*; do
  if [ -d $f ] && [ -f $f/platinfo ]; then
    run $f >`basename $f`.out 2>`basename $f`.err
  fi
done
