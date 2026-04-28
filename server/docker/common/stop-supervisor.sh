#!/usr/bin/env sh

printf "READY\n"

while read line; do
  echo "Processing Event: $line" >&2
  kill $PPID
done < /dev/stdin
