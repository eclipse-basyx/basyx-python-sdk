"""
This helper script checks that the provided `min_version` and `max_version` are supported and released, respectively,
using the API from the great https://github.com/endoflife-date/endoflife.date project.
"""
import argparse
import sys
import requests
from packaging.version import InvalidVersion
from datetime import datetime

def main(min_version: str, max_version: str) -> None:
    # Fetch supported Python versions and check min/max versions
    try:
        response = requests.get("https://endoflife.date/api/python.json")
        response.raise_for_status()
        eol_data = response.json()
        eol_versions = {entry["cycle"]: {"eol": entry["eol"], "releaseDate": entry["releaseDate"]} for entry in eol_data}

        # Get current date to compare with EoL and release dates
        current_date = datetime.now().date()

        # Check min_version EoL status
        min_eol_date = eol_versions.get(min_version, {}).get("eol")
        if min_eol_date and datetime.strptime(min_eol_date, "%Y-%m-%d").date() <= current_date:
            print(f"Error: min_version {min_version} has reached End-of-Life.")
            sys.exit(1)

        # Check max_version EoL and release status
        max_info = eol_versions.get(max_version)
        if max_info:
            max_eol_date = max_info["eol"]
            max_release_date = max_info["releaseDate"]

            # Check if max_version has a release date in the future
            if max_release_date and datetime.strptime(max_release_date, "%Y-%m-%d").date() > current_date:
                print(f"Error: max_version {max_version} has not been officially released yet.")
                sys.exit(1)

            # Check if max_version has reached EoL
            if max_eol_date and datetime.strptime(max_eol_date, "%Y-%m-%d").date() <= current_date:
                print(f"Error: max_version {max_version} has reached End-of-Life.")
                sys.exit(1)

    except requests.RequestException:
        print("Error: Failed to fetch Python version support data.")
        sys.exit(1)

    print(f"Version check passed: min_version [{min_version}] is supported "
          f"and max_version [{max_version}] is released.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Python version support and alignment with pyproject.toml.")
    parser.add_argument("min_version", help="The minimum Python version.")
    parser.add_argument("max_version", help="The maximum Python version.")
    args = parser.parse_args()

    try:
        main(args.min_version, args.max_version)
    except InvalidVersion:
        print("Error: Invalid version format provided.")
        sys.exit(1)
