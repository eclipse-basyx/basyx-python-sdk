#!/usr/bin/env bash
# Usage: ./set_copyright_year.sh [PATHS]
#
# This is a small script for setting the correct copyright year
# for each given file (i.e. the year the file was last changed).
# Instead of file paths you can also specify directories, in which
# case the script will attempt to set the copyright year for all
# files in the given directories. Globbing is also possible.
#
# The script will check the first two lines for a copyright
# notice (in case the first line is a shebang).

while read -rd $'\0' year file; do
    sed -i "1,2s/^\(# Copyright \)[[:digit:]]\{4,\}/\1$year/" "$file"
done < <(git ls-files -z "$@" | xargs -0I{} git log -1 -z --format="%ad {}" --date="format:%Y" "{}")
