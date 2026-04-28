#!/usr/bin/env bash
# Usage: ./set_copyright_year.sh [PATHS]
#
# This is a small script for setting the correct copyright year
# for each given source file (i.e. the year the file was last
# changed) and LICENSE file (i.e. the latest modification year
# across all files). Instead of file paths you can also specify
# directories, in which case the script will attempt to set the
# copyright year for all files in the given directories.
# Globbing is also possible.
#
# In source files, the script checks the first two lines for a
# copyright notice (in case the first line is a shebang).
# In the LICENSE file, it checks the first three lines for a
# copyright notice containing a year range.
#
# Run this script with --check to have it raise an error if it
# would change anything.

# Initialise a variable to track if any error occurred
EXIT_CODE=0

# Set CHECK_MODE based on whether --check is passed
CHECK_MODE=false
if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
    shift # Remove --check from the arguments
fi

# Initialise a variable to track the latest modification year across all files
max_year=""

# Validate the copyright year of each source file
while read -rd $'\0' year file; do

    # Extract the current modification year and update variable
    if [[ -z "$max_year" || "$year" -gt "$max_year" ]]; then
        max_year="$year"
    fi

    # Extract the first year from the copyright notice
    current_year=$(sed -n '1,2s/^\(# Copyright (c) \)\([[:digit:]]\{4,\}\).*/\2/p' "$file")

    # Skip the source file if no year is found
    if [[ -z "$current_year" ]]; then
        continue
    fi

    # If in check mode, report the incorrect copyright year
    if $CHECK_MODE && [[ "$current_year" != "$year" ]]; then
        echo "Error: Copyright year mismatch in file $file. Expected $year, found $current_year."
        # Set EXIT_CODE to 1 to indicate mismatch
        EXIT_CODE=1
    fi

    # Otherwise rewrite the incorrect copyright year
    if ! $CHECK_MODE && [[ "$current_year" != "$year" ]]; then
        sed -i "1,2s/^\(# Copyright (c) \)[[:digit:]]\{4,\}/\1$year/" "$file"
        echo "Updated copyright year in $file"
    fi
done < <(git ls-files -z "$@" | xargs -0I{} git log -1 -z --format="%cd {}" --date="format:%Y" -- "{}")

# Validate the copyright year of the LICENSE file
license_current_year=$(sed -n '1,3{s/^Copyright (c) [[:digit:]]\{4\}-\([[:digit:]]\{4\}\).*/\1/p}' LICENSE)

if $CHECK_MODE && [[ -n "$license_current_year" && "$license_current_year" != "$max_year" ]]; then
    echo "Error: Copyright year mismatch in file LICENSE. Expected $max_year, found $license_current_year."
    EXIT_CODE=1
fi

if ! $CHECK_MODE && [[ -n "$license_current_year" && "$license_current_year" != "$max_year" ]]; then
    sed -i "1,3s/^\(Copyright (c) [[:digit:]]\{4\}-\)[[:digit:]]\{4\}/\1$max_year/" LICENSE
    echo "Updated copyright year in LICENSE"
fi

exit $EXIT_CODE
