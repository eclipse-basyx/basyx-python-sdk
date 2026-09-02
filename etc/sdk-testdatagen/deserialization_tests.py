import argparse
import enum
import logging
import re
import subprocess
import sys
import traceback
from collections import Counter
from pathlib import Path
from typing import Optional

from basyx.aas import adapter
from basyx.aas.model import AASConstraintViolation

logger = logging.getLogger(__name__)

class TestResult(enum.Enum):
    SUCCESS = "Success :white_check_mark:"
    NOT_IMPLEMENTED = "Not Implemented :warning:"
    FAILED = "Failed :x:"
    UNEXPECTED_ERROR = "Unexpected Error :exclamation:"
    def __format__(self, format_spec):
        return f"{self.value}"

def sanitize_name(name: str, max_len: int = 120) -> str:
    pattern = r'[<>:"/\\|?*\x00-\x1f\s\'{}\(\)\[\]]'
    name = re.sub(pattern, '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')[:max_len]

def write_error_report(file_type, example_file, rel_path, error_dir, tb):
    error_dir.mkdir(parents=True, exist_ok=True)
    # Use the full relative path (not just the stem) to avoid collisions: generated example sets reuse
    # the same filenames across many different subdirectories.
    error_file = error_dir / f"{sanitize_name(str(rel_path))}.txt"

    content = example_file.read_text(encoding="utf-8")
    error_output = f"=== {file_type.upper()} File: {rel_path} ===\n{content}\n\n=== Stacktrace ====\n{tb}"
    error_file.write_text(error_output, encoding="utf-8")


def run_example_test(
    file_type, example_file, read_fn, base_path=None, output_dir=None, is_xml=False
) -> tuple[TestResult, str]:
    rel_path = example_file.relative_to(base_path) if base_path else example_file

    try:
        read_fn(example_file)
        return TestResult.SUCCESS, ""
    except (KeyError, TypeError, ValueError, AASConstraintViolation) as ex:
        tb = traceback.format_exc()
        error_msg = extract_error_message(ex) if is_xml else str(ex).split(">>>")[0].strip()
        logger.error(f"[{file_type.upper()}] ERROR on {rel_path}: {error_msg}")

        if output_dir:
            error_dir = output_dir / file_type / sanitize_name(error_msg)
            write_error_report(file_type, example_file, rel_path, error_dir, tb)
        return TestResult.FAILED, error_msg

    except NotImplementedError as ex:
        tb = traceback.format_exc()
        error_msg = extract_error_message(ex) if is_xml else str(ex).split(">>>")[0].strip()
        logger.warning(f"[{file_type.upper()}] NOT_IMPLEMENTED on {rel_path}: {error_msg}")

        if output_dir:
            error_dir = output_dir / file_type / "NotImplementedError" / sanitize_name(error_msg)
            write_error_report(file_type, example_file, rel_path, error_dir, tb)
        return TestResult.NOT_IMPLEMENTED, error_msg

    except Exception as ex:
        # Catch-all so an exception type not (yet) anticipated by the except clauses above (e.g. thrown by a
        # future implementation change) fails just this one example instead of aborting the whole run.
        # Deliberately not `except BaseException`, so KeyboardInterrupt/SystemExit still propagate.
        tb = traceback.format_exc()
        error_msg = extract_error_message(ex) if is_xml else str(ex).split(">>>")[0].strip()
        logger.error(f"[{file_type.upper()}] UNEXPECTED {type(ex).__name__} on {rel_path}: {error_msg}")

        if output_dir:
            error_dir = (
                    output_dir
                    / file_type
                    / "UnexpectedError"
                    / sanitize_name(type(ex).__name__)
                    / sanitize_name(error_msg)
            )
            write_error_report(file_type, example_file, rel_path, error_dir, tb)
        return TestResult.UNEXPECTED_ERROR, error_msg

def extract_error_message(ex):
    message = str(ex)
    cause = ex.__cause__
    while cause is not None:
        message = f"{message} -> {cause}"
        cause = cause.__cause__
    return re.sub(r'on line [0-9]+', "", message.split("->")[-1]).strip()


def test_json_example(
    example_file: Path, base_path: Optional[Path] = None, output_dir: Optional[Path] = None
) -> tuple[TestResult, str]:
    """
    Attempts to read and deserialize an example file. Reports the status and saves information to output path.

    :param example_file: File which contains the example that should be deserialized
    :param base_path: Base directory to compute relative paths
    :param output_dir: Path to store the failed outputs
    :return: bool that indicates if the example was successfully deserialized
    """
    return run_example_test(
        file_type="json",
        example_file=example_file,
        read_fn=lambda f: adapter.json.read_aas_json_file(f, failsafe=False),
        base_path=base_path,
        output_dir=output_dir,
    )


def test_xml_example(
        example_file: Path, base_path: Optional[Path] = None, output_dir: Optional[Path] = None
) -> tuple[TestResult, str]:
    """
    Attempts to read and deserialize an XML example file. Reports the status and saves information to output path.

    :param example_file: File which contains the example that should be deserialized
    :param base_path: Base directory to compute relative paths
    :param output_dir: Path to store the failed outputs
    :return: bool that indicates if the example was successfully deserialized
    """
    return run_example_test(
        file_type="xml",
        example_file=example_file,
        read_fn=lambda f: adapter.xml.read_aas_xml_file(f, failsafe=False),
        base_path=base_path,
        output_dir=output_dir,
        is_xml=True,
    )

def summarize_output(
        test_results: dict[str, Counter[tuple[TestResult, str]]], example_path: Path, output_file: Path
) -> None:
    """Builds a Markdown summary of the failures recorded in `test_results`."""

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
            raise ValueError("Exaple files do not stem from aas-specs-metamodel repository")
        metamodel_tag = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=example_path, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        metamodel_tag = "unknown"

    sections = [f"## AAS testdatagen results (metamodel: `{metamodel_tag}`)",
                f"Summary of the results from testing the SDK implementation (`{sdk_commit}`) against the example files"
                f"from `aas-specs-metamodel` (version: `{metamodel_tag}`). For detailed information on each failed test"
                f"consider the artifact uploaded with this job."]

    for format_name in test_results.keys():
        format_results = test_results[format_name]
        sections.append(f"### {format_name}")

        totals: dict[TestResult, int] = {}
        for category, err_msg in format_results.keys():
            totals[category] = totals.get(category, 0) + format_results[category, err_msg]
        sections.append(" · ".join(f"{category} : {count}" for category, count in totals.items()))

        total_failed = sum((value for category, value in totals.items() if category != TestResult.SUCCESS))
        table_lines = [
            "<details>",
            f"<summary>Error groups ({total_failed})</summary>",
            "",
            "| Category | Group | Count |",
            "|---|---|---|",
        ]
        table_lines += [f"| {category} | {err_msg} | {count} |"
                        for (category, err_msg), count in format_results.most_common()
                        if category != TestResult.SUCCESS
                        ]
        table_lines += ["", "</details>"]
        sections.append("\n".join(table_lines))

    output_file.write_text("\n\n".join(sections))

def main(example_path_str: str, output_path_str: Optional[str], summary_path_str: Optional[str]) -> None:
    example_path = Path(example_path_str)
    output_path = Path(output_path_str) if output_path_str else None
    summary_path = Path(summary_path_str) if summary_path_str else None

    if not example_path.exists():
        logger.error(f"Provided path for examples does not exist: {example_path}")
        sys.exit(1)

    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)

    test_configs = [
        ("JSON", example_path / "json" / "examples" / "generated", "*.json", test_json_example),
        ("XML", example_path / "xml" / "examples" / "generated", "*.xml", test_xml_example),
    ]

    test_results: dict[str, Counter[tuple[TestResult, str]]] = dict()
    total_failed = 0
    for name, directory, glob_pattern, test_fn in test_configs:
        format_results: Counter[tuple[TestResult, str]] = Counter()
        for test_file in sorted(directory.glob(f"**/{glob_pattern}")):
            test_result = test_fn(test_file, directory, output_path)
            format_results[test_result] += 1

        test_results[name] = format_results
        failed = sum((format_results[result, err_msg]
                      for result, err_msg in format_results.keys()
                      if result not in (TestResult.SUCCESS, TestResult.NOT_IMPLEMENTED)
                      ))
        total_failed += failed
        total = sum(format_results.values())
        if failed == 0:
            logger.info(f"No {name} tests out of {total:d} failed")
        else:
            logger.error(f"Failed {failed:d}/{total:d} {name.lower()} tests")

    if summary_path is not None:
        summarize_output(test_results, example_path, summary_path)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", required=True, help="path to examples directory")
    parser.add_argument("--output", required=False, help="path to output directory")
    parser.add_argument("--summary", required=False, help="file to write summary to")
    args = parser.parse_args()

    main(args.examples, args.output, args.summary)
