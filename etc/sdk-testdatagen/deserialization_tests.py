# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This script tests the deserialization of the BaSyx Python SDK against the example files that
`aas-core-testdatagen` generates. The `aas-specs-metamodel` repository supplies these example files.

The script reads each JSON and XML example file with the SDK adapters. It puts the result of each test into one of
the categories in `TestResult`. Error groups listed in the known deviations file (`known_deviations.toml`) are
categorized as `KNOWN_DEVIATION`. For each test that does not succeed, the script can write a report that contains the
example file and the stack trace. It can also write a Markdown summary, which the CI shows as the GitHub job summary.

The script exits with code 1 if at least one test has a result in `FAILING_RESULTS`, if no example files are found for a
format, or if a known deviation did not occur (stale known deviation).

For the usage and the arguments, refer to the `Readme.md` in this directory.
"""
import argparse
import enum
import logging
import re
import subprocess
import sys
import tomllib
import traceback
from collections import Counter
from pathlib import Path
from typing import Callable, Optional, Sequence

from basyx.aas import adapter
from basyx.aas.model import AASConstraintViolation

logger = logging.getLogger(__name__)

class TestResult(enum.Enum):
    SUCCESS = "Success :white_check_mark:"
    NOT_IMPLEMENTED = "Not Implemented :warning:"
    FAILED = "Failed :x:"
    UNEXPECTED_ERROR = "Unexpected Error :exclamation:"
    KNOWN_DEVIATION = "Known Deviation :information_source:"
    def __format__(self, format_spec):
        return f"{self.value}"

# Results that count as failures, both in the summary and for the exit code of the script
FAILING_RESULTS = (TestResult.FAILED, TestResult.UNEXPECTED_ERROR)

# Formats that are tested, as used for the tables in the known deviations file
FORMATS = ("JSON", "XML")
KNOWN_DEVIATIONS_FILE = Path(__file__).parent / "known_deviations.toml"
ISSUE_LINK_RE = re.compile(r"^https?://\S+$")


def load_known_deviations(path: Path) -> dict[str, dict[str, str]]:
    """
    Reads and validates the known deviations file.

    :param path: Path of the TOML file that lists the known deviations
    :return: Mapping from format to a mapping from error group to issue link
    :raises ValueError: If the content of the file is invalid
    """
    with path.open("rb") as f:
        data = tomllib.load(f)

    unknown_formats = set(data) - set(FORMATS)
    if unknown_formats:
        raise ValueError(f"Unknown formats {sorted(unknown_formats)}, expected one of {list(FORMATS)}")

    known_deviations: dict[str, dict[str, str]] = {format_name: {} for format_name in FORMATS}
    for format_name, entries in data.items():
        if not isinstance(entries, list):
            raise ValueError(f"'{format_name}' must be an array of tables ([[{format_name}]])")
        for index, entry in enumerate(entries):
            location = f"[[{format_name}]] entry {index + 1}"
            if not isinstance(entry, dict) or set(entry) != {"group", "issue"}:
                raise ValueError(f"{location} must have exactly the keys 'group' and 'issue'")
            group, issue = entry["group"], entry["issue"]
            if not isinstance(group, str) or not group.strip():
                raise ValueError(f"{location}: 'group' must be a non-empty string")
            if not isinstance(issue, str) or not ISSUE_LINK_RE.match(issue):
                raise ValueError(f"{location}: 'issue' must be a link, got {issue!r}")
            if group in known_deviations[format_name]:
                raise ValueError(f"{location}: duplicate group {group!r}")
            known_deviations[format_name][group] = issue
    return known_deviations


def sanitize_name(name: str, max_len: int = 120) -> str:
    pattern = r'[<>:"/\\|?*\x00-\x1f\s\'{}\(\)\[\]]'
    name = re.sub(pattern, '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')[:max_len]

def write_error_report(file_type: str, example_file: Path, rel_path: Path, error_dir: Path, tb: str) -> None:
    """
    Writes a report with the content of the example file and the stack trace of the error.

    :param file_type: Format of the example file (`json` or `xml`)
    :param example_file: File which contains the example that failed
    :param rel_path: Path of the example file relative to the examples directory, used to name the report
    :param error_dir: Directory to write the report to
    :param tb: Formatted stack trace of the error
    """
    error_dir.mkdir(parents=True, exist_ok=True)
    # Use the full relative path (not just the stem) to avoid collisions: generated example sets reuse
    # the same filenames across many different subdirectories.
    error_file = error_dir / f"{sanitize_name(str(rel_path))}.txt"

    content = example_file.read_text(encoding="utf-8")
    error_output = f"=== {file_type.upper()} File: {rel_path} ===\n{content}\n\n=== Stacktrace ====\n{tb}"
    error_file.write_text(error_output, encoding="utf-8")


def run_example_test(
    file_type: str,
    example_file: Path,
    read_fn: Callable[[Path], object],
    base_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    is_xml: bool = False,
    known_deviations: Optional[dict[str, str]] = None,
) -> tuple[TestResult, str]:
    """
    Deserializes an example file with `read_fn` and categorizes the outcome. Writes an error report to `output_dir`
    for each test that does not succeed.

    :param file_type: Format of the example file (`json` or `xml`), used for logging and the report directory
    :param example_file: File which contains the example that should be deserialized
    :param read_fn: Function that deserializes the example file
    :param base_path: Base directory to compute relative paths
    :param output_dir: Path to store the failed outputs
    :param is_xml: If True, the error message is extracted from the chain of causes of the exception
    :param known_deviations: Mapping from error group to issue link. Errors of these groups are categorized as
        `KNOWN_DEVIATION`, regardless of the type of the exception.
    :return: Result of the test and the error message (empty on success)
    """
    rel_path = example_file.relative_to(base_path) if base_path else example_file

    def handle_error(ex: Exception, result: TestResult, report_subdirs: Sequence[str]) -> tuple[TestResult, str]:
        # Must be called from within the except clause, so that the stack trace is still available
        tb = traceback.format_exc()
        error_msg = extract_error_message(ex) if is_xml else str(ex).split(">>>")[0].strip()

        if known_deviations and error_msg in known_deviations:
            result, report_subdirs = TestResult.KNOWN_DEVIATION, ("KnownDeviation",)
            logger.info(f"[{file_type.upper()}] KNOWN_DEVIATION on {rel_path}: {error_msg} "
                        f"(see {known_deviations[error_msg]})")
        elif result == TestResult.NOT_IMPLEMENTED:
            logger.warning(f"[{file_type.upper()}] NOT_IMPLEMENTED on {rel_path}: {error_msg}")
        elif result == TestResult.UNEXPECTED_ERROR:
            logger.error(f"[{file_type.upper()}] UNEXPECTED {type(ex).__name__} on {rel_path}: {error_msg}")
        else:
            logger.error(f"[{file_type.upper()}] ERROR on {rel_path}: {error_msg}")

        if output_dir:
            error_dir = output_dir.joinpath(file_type, *report_subdirs, sanitize_name(error_msg))
            write_error_report(file_type, example_file, rel_path, error_dir, tb)
        return result, error_msg

    try:
        read_fn(example_file)
        return TestResult.SUCCESS, ""
    except (KeyError, TypeError, ValueError, AASConstraintViolation) as ex:
        return handle_error(ex, TestResult.FAILED, ())
    except NotImplementedError as ex:
        return handle_error(ex, TestResult.NOT_IMPLEMENTED, ("NotImplementedError",))
    except Exception as ex:
        # Catch-all so an exception type not (yet) anticipated by the except clauses above (e.g. thrown by a
        # future implementation change) fails just this one example instead of aborting the whole run.
        # Deliberately not `except BaseException`, so KeyboardInterrupt/SystemExit still propagate.
        return handle_error(ex, TestResult.UNEXPECTED_ERROR, ("UnexpectedError", sanitize_name(type(ex).__name__)))

def extract_error_message(ex: BaseException) -> str:
    """
    Extracts the message of the innermost cause of an exception, without line numbers, so that errors of different
    example files can be grouped.

    :param ex: Exception to extract the message from
    :return: Message of the innermost cause
    """
    message = str(ex)
    cause = ex.__cause__
    while cause is not None:
        message = f"{message} -> {cause}"
        cause = cause.__cause__
    return re.sub(r'on line [0-9]+', "", message.split("->")[-1]).strip()


def test_json_example(
    example_file: Path,
    base_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    known_deviations: Optional[dict[str, str]] = None,
) -> tuple[TestResult, str]:
    """
    Attempts to read and deserialize an example file. Reports the status and saves information to output path.

    :param example_file: File which contains the example that should be deserialized
    :param base_path: Base directory to compute relative paths
    :param output_dir: Path to store the failed outputs
    :param known_deviations: Mapping from error group to issue link of the known deviations
    :return: Result of the test and the error message (empty on success)
    """
    return run_example_test(
        file_type="json",
        example_file=example_file,
        read_fn=lambda f: adapter.json.read_aas_json_file(f, failsafe=False),
        base_path=base_path,
        output_dir=output_dir,
        known_deviations=known_deviations,
    )


def test_xml_example(
    example_file: Path,
    base_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    known_deviations: Optional[dict[str, str]] = None,
) -> tuple[TestResult, str]:
    """
    Attempts to read and deserialize an XML example file. Reports the status and saves information to output path.

    :param example_file: File which contains the example that should be deserialized
    :param base_path: Base directory to compute relative paths
    :param output_dir: Path to store the failed outputs
    :param known_deviations: Mapping from error group to issue link of the known deviations
    :return: Result of the test and the error message (empty on success)
    """
    return run_example_test(
        file_type="xml",
        example_file=example_file,
        read_fn=lambda f: adapter.xml.read_aas_xml_file(f, failsafe=False),
        base_path=base_path,
        output_dir=output_dir,
        is_xml=True,
        known_deviations=known_deviations,
    )

def summarize_output(
        test_results: dict[str, Counter[tuple[TestResult, str]]],
        known_deviations: dict[str, dict[str, str]],
        stale_deviations: dict[str, dict[str, str]],
        example_path: Path,
        output_file: Path,
) -> None:
    """
    Builds a Markdown summary of the failures recorded in `test_results`.

    :param test_results: Count of each pair of result and error group, per format
    :param known_deviations: Mapping from error group to issue link of the known deviations, per format
    :param stale_deviations: Known deviations that did not occur, per format
    :param example_path: Path of the examples directory, used to determine the version of the example files
    :param output_file: File to write the summary to
    """

    # Get commit hash of sdk
    try:
        sdk_commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sdk_commit = "unknown"

    # Get version of example files (if in git repo)
    try:
        metamodel_origin = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=example_path, capture_output=True, text=True, check=True
        ).stdout.strip()

        if "aas-specs-metamodel" not in metamodel_origin:
            raise ValueError("Example files do not stem from aas-specs-metamodel repository")
        metamodel_tag = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=example_path, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        metamodel_tag = "unknown"

    sections = [f"## AAS testdatagen results (metamodel: `{metamodel_tag}`)",
                f"Summary of the results from testing the SDK implementation (`{sdk_commit}`) against the example "
                f"files from `aas-specs-metamodel` (version: `{metamodel_tag}`). For detailed information on each "
                f"failed test consider the artifact uploaded with this job."]

    for format_name in test_results.keys():
        format_results = test_results[format_name]
        format_known_deviations = known_deviations[format_name]
        sections.append(f"### {format_name}")
        if not format_results:
            sections.append(f":x: No {format_name} example files found")
        else:
            totals: dict[TestResult, int] = {}
            for category, err_msg in format_results.keys():
                totals[category] = totals.get(category, 0) + format_results[category, err_msg]
            sections.append(" · ".join(f"{category} : {count}" for category, count in totals.items()))

            total_failed = sum(value for category, value in totals.items() if category in FAILING_RESULTS)
            total_not_implemented = totals.get(TestResult.NOT_IMPLEMENTED, 0)
            total_known_deviations = totals.get(TestResult.KNOWN_DEVIATION, 0)
            table_lines = [
                "<details>",
                f"<summary>Error groups ({total_failed} failed, {total_not_implemented} not implemented, "
                f"{total_known_deviations} known deviations)</summary>",
                "",
                "| Category | Group | Issue | Count |",
                "|---|---|---|---|",
            ]
            table_lines += [f"| {category} | {err_msg} | "
                            f"{format_known_deviations[err_msg] if category == TestResult.KNOWN_DEVIATION else ''} | "
                            f"{count} |"
                            for (category, err_msg), count in format_results.most_common()
                            if category != TestResult.SUCCESS
                            ]
            table_lines += ["", "</details>"]
            sections.append("\n".join(table_lines))

        format_stale_deviations = stale_deviations[format_name]
        if format_stale_deviations:
            stale_lines = [
                "#### Stale known deviations :x:",
                "These known deviations did not occur. Remove them from the known deviations file.",
                "",
                "| Group | Issue |",
                "|---|---|",
            ]
            stale_lines += [f"| {group} | {issue} |" for group, issue in format_stale_deviations.items()]
            sections.append("\n".join(stale_lines))

    output_file.write_text("\n\n".join(sections))

def main(
        example_path_str: str,
        output_path_str: Optional[str],
        summary_path_str: Optional[str],
        known_deviations_path_str: Optional[str],
) -> None:
    example_path = Path(example_path_str)
    output_path = Path(output_path_str) if output_path_str else None
    summary_path = Path(summary_path_str) if summary_path_str else None
    known_deviations_path = Path(known_deviations_path_str) if known_deviations_path_str else KNOWN_DEVIATIONS_FILE

    if not example_path.exists():
        logger.error(f"Provided path for examples does not exist: {example_path}")
        sys.exit(1)

    # A missing default file means that there are no known deviations, a missing file passed explicitly is an error
    if known_deviations_path_str is None and not known_deviations_path.exists():
        known_deviations: dict[str, dict[str, str]] = {format_name: {} for format_name in FORMATS}
    else:
        try:
            known_deviations = load_known_deviations(known_deviations_path)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as ex:
            logger.error(f"Invalid known deviations file {known_deviations_path}: {ex}")
            sys.exit(1)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

    test_configs = [
        ("JSON", example_path / "json" / "examples" / "generated", "*.json", test_json_example),
        ("XML", example_path / "xml" / "examples" / "generated", "*.xml", test_xml_example),
    ]

    test_results: dict[str, Counter[tuple[TestResult, str]]] = dict()
    stale_deviations: dict[str, dict[str, str]] = dict()
    total_failed = 0
    run_failed = False
    for name, directory, glob_pattern, test_fn in test_configs:
        test_files = sorted(directory.glob(f"**/{glob_pattern}"))
        if not test_files:
            logger.error(f"No {name} example files found in {directory}")
            run_failed = True

        format_results: Counter[tuple[TestResult, str]] = Counter()
        for test_file in test_files:
            test_result = test_fn(test_file, directory, output_path, known_deviations[name])
            format_results[test_result] += 1

        test_results[name] = format_results
        failed = sum((format_results[result, err_msg]
                      for result, err_msg in format_results.keys()
                      if result in FAILING_RESULTS
                      ))
        total_failed += failed
        total = sum(format_results.values())
        if failed == 0:
            logger.info(f"No {name} tests out of {total:d} failed")
        else:
            logger.error(f"Failed {failed:d}/{total:d} {name.lower()} tests")

        occurred_deviations = {err_msg for result, err_msg in format_results if result == TestResult.KNOWN_DEVIATION}
        stale_deviations[name] = {group: issue for group, issue in known_deviations[name].items()
                                  if group not in occurred_deviations}
        for group, issue in stale_deviations[name].items():
            logger.error(f"Stale known {name} deviation did not occur: {group} (see {issue})")
            run_failed = True

    if summary_path is not None:
        summarize_output(test_results, known_deviations, stale_deviations, example_path, summary_path)
    sys.exit(1 if total_failed > 0 or run_failed else 0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", required=True, help="path to examples directory")
    parser.add_argument("--output", required=False, help="path to output directory")
    parser.add_argument("--summary", required=False, help="file to write summary to")
    parser.add_argument("--known-deviations", required=False,
                        help=f"TOML file that lists the known deviations "
                             f"(default: {KNOWN_DEVIATIONS_FILE.name} next to this script)")
    args = parser.parse_args()

    main(args.examples, args.output, args.summary, args.known_deviations)
