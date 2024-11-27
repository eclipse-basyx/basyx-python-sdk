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
    # Extract the first year from the copyright notice
    current_year=$(sed -n '1,2s/^\(# Copyright (c) \)[^0-9]*\([0-9]\{4\}\)\([^\n]*\)/\2/p' "$file")

    if $CHECK_MODE && [[ "$current_year" != "$year" ]]; then
        echo "Error: Copyright year mismatch in file $file. Expected $year, found $current_year."
        exit 1
    fi

    if ! $CHECK_MODE && [[ "$current_year" != "$year" ]]; then
        sed -i "1,2s/^\(# Copyright (c) \)[[:digit:]]\{4,\}/\1$year/" "$file"
        echo "Updated copyright year in $file"
    fi
done < <(git ls-files -z "$@" | xargs -0I{} git log -1 -z --format="%ad {}" --date="format:%Y" "{}")

