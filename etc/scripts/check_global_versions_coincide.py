"""
This script dynamically verifies that the modules respect the versions defined in the global versions.toml.
The python version is handled separately (checked against `requires-python` in every pyproject and against the
`FROM python:X.Y` line of every listed Dockerfile).
The tools section is checked against all toml files.
The config section is checked against a config file containing the name in its path.
All other sections are ignored as they are intended for direct consumption elsewhere (mostly CI).
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text())
    except FileNotFoundError:
        print(f"Error: `{path}` not found.", file=sys.stderr)
        sys.exit(1)


def _dev_deps(pyproject: dict[str, Any]) -> list[str]:
    return pyproject.get("project", {}).get("optional-dependencies", {}).get("dev", [])


def check_python(versions: dict[str, Any], pyproject_paths: list[Path], repo_root: Path) -> list[str]:
    """Verify `python.min` matches `[project] requires-python = ">=<min>"` in every pyproject."""
    min_version = versions.get("python", {}).get("min")
    if not min_version:
        return ["versions.toml: missing `python.min`"]

    expected = f">={min_version}"
    errors: list[str] = []
    for path in pyproject_paths:
        pyproject = _load_toml(path)
        actual = pyproject.get("project", {}).get("requires-python")
        display = path.relative_to(repo_root)
        if actual is None:
            errors.append(f"{display}: missing `project.requires-python`")
        elif actual != expected:
            errors.append(f"{display}: `requires-python` is `{actual}`, expected `{expected}`")
    return errors


def check_dev_tools(versions: dict[str, Any], pyproject_paths: list[Path], repo_root: Path) -> list[str]:
    """Verify each `dev_tools.<name> = <version>` appears as `<name>==<version>` in every pyproject's dev deps."""
    tools: dict[str, str] = versions.get("dev_tools", {})
    errors: list[str] = []

    for path in pyproject_paths:
        pyproject = _load_toml(path)
        deps = _dev_deps(pyproject)
        display = path.relative_to(repo_root)

        for tool, version in tools.items():
            pattern = re.compile(rf"^{re.escape(tool)}\s*==\s*{re.escape(version)}$")
            if not any(pattern.match(dep) for dep in deps):
                errors.append(
                    f"{display}: dev dependency `{tool}=={version}` missing "
                    f"from `[project.optional-dependencies].dev` (found: {deps})"
                )
    return errors


def check_dockerfiles(versions: dict[str, Any], dockerfile_paths: list[Path], repo_root: Path) -> list[str]:
    """
    Verify the `FROM python:X.Y[-...]` line of every listed Dockerfile has an `X.Y` that falls
    within [python.min, python.max].
    """
    min_str = versions.get("python", {}).get("min")
    max_str = versions.get("python", {}).get("max")
    if not min_str or not max_str:
        return ["versions.toml: `python.min` / `python.max` required for Dockerfile checks"]

    min_ver = tuple(int(p) for p in min_str.split("."))
    max_ver = tuple(int(p) for p in max_str.split("."))
    from_pattern = re.compile(r"^\s*FROM\s+python:(\d+)\.(\d+)", re.MULTILINE)

    errors: list[str] = []
    for path in dockerfile_paths:
        try:
            text = path.read_text()
        except FileNotFoundError:
            errors.append(f"{path.relative_to(repo_root)}: Dockerfile not found")
            continue

        match = from_pattern.search(text)
        display = path.relative_to(repo_root)
        if not match:
            errors.append(f"{display}: no `FROM python:X.Y` line found")
            continue

        found = (int(match.group(1)), int(match.group(2)))
        found_str = f"{found[0]}.{found[1]}"
        if found < min_ver or found > max_ver:
            errors.append(
                f"{display}: base image `python:{found_str}` outside supported "
                f"range [{min_str}, {max_str}]"
            )
    return errors


def check_configs(versions: dict[str, Any], config_paths: list[Path], repo_root: Path) -> list[str]:
    """
    Verify each `config.<name>.<key> = <value>` appears in a listed config file whose path
    contains `<name>`. Config files are loaded as TOML.
    """
    config_section: dict[str, dict[str, Any]] = versions.get("config", {})
    errors: list[str] = []

    for module_name, expected_entries in config_section.items():
        matches = [p for p in config_paths if module_name in str(p)]
        if not matches:
            errors.append(
                f"config.{module_name}: no config file in `configuration_locations.configs` "
                f"has `{module_name}` in its path"
            )
            continue
        if len(matches) > 1:
            errors.append(
                f"config.{module_name}: ambiguous — multiple config files match "
                f"`{module_name}`: {[str(m.relative_to(repo_root)) for m in matches]}"
            )
            continue

        config_path = matches[0]
        loaded = _load_toml(config_path)
        display = config_path.relative_to(repo_root)

        for key, expected in expected_entries.items():
            actual = loaded.get(key)
            if actual is None:
                errors.append(f"{display}: missing entry `{key}` (expected `{expected!r}`)")
            elif actual != expected:
                errors.append(f"{display}: `{key}` is `{actual!r}`, expected `{expected!r}`")
    return errors


def _resolve_paths(rel_paths: list[str], repo_root: Path) -> list[Path]:
    return [(repo_root / p).resolve() for p in rel_paths]


def main(versions_toml_path: Path) -> int:
    versions = _load_toml(versions_toml_path)
    repo_root = versions_toml_path.resolve().parent

    locations = versions.get("configuration_locations", {})
    pyproject_paths = _resolve_paths(locations.get("pyprojects", []), repo_root)
    config_paths = _resolve_paths(locations.get("configs", []), repo_root)
    dockerfile_paths = _resolve_paths(locations.get("dockerfiles", []), repo_root)

    errors: list[str] = []
    errors += check_python(versions, pyproject_paths, repo_root)
    errors += check_dev_tools(versions, pyproject_paths, repo_root)
    errors += check_dockerfiles(versions, dockerfile_paths, repo_root)
    errors += check_configs(versions, config_paths, repo_root)

    if errors:
        print("Version drift:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"Success: `{versions_toml_path.name}` coincides with "
        f"{len(pyproject_paths)} pyproject.toml file(s), "
        f"{len(dockerfile_paths)} Dockerfile(s), and "
        f"{len(config_paths)} config file(s)."
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--versions",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "versions.toml",
        help="Path to versions.toml.",
    )
    args = parser.parse_args()
    sys.exit(main(args.versions))
