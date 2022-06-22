#!/bin/bash

if [ $# -lt 2 ]; then
  echo "Usage: $0 <pp/pk command> <checkpoint dir>"
  exit 1
fi

cmd="$1"
if [[ $cmd == *"pk"* ]]; then
  prefix="-r"
fi
checkpoint_dir=$2

function run() {
  echo "Running $1" 1>&2
  $cmd -s $prefix $1 --fuzzy-strace
  ret=$?
  if [ $ret -ne 0 ]; then
    echo "error, return code $ret" 1>&2
  fi
}

for f in $checkpoint_dir/*/; do
  if [ -d $f ] && [ -f $f/platinfo ]; then
    run $f >`basename $f`.out 2>`basename $f`.err
  fi
done
