# AGENTS.md

Rules for AI agents working in this repository. They add to [CONTRIBUTING.md](CONTRIBUTING.md),
which you must follow.

## Rules for AI contributions
- Name the model and its version in the PR description, e.g. `Claude Opus 5.5`. PRs that we believe were made with
  AI without this statement are rejected entirely.
- Only humans accept and merge PRs (see [Merging Pull Requests](CONTRIBUTING.md#merging-pull-requests)). Leave
  approving and merging to the maintainers.
- Keep this file current: if your change makes anything here wrong or incomplete, update `AGENTS.md` in the same PR.

## Before you start
- Read [CONTRIBUTING.md](CONTRIBUTING.md) and the `README.md` of the repository root and of each package you change.
- If you are blocked, or the specification is ambiguous, stop and ask. In a PR, state the open question instead of
  guessing.

## Monorepo
Each package has its own `pyproject.toml`. Run all commands from the package directory.

| Package            | Source dir             | Depends on |
|--------------------|------------------------|------------|
| `sdk/`             | `basyx/`               | -          |
| `server/`          | `app/`                 | `sdk/`     |
| `compliance_tool/` | `aas_compliance_tool/` | `sdk/`     |

## Workflow
- Use test-driven development: write a test that fails, implement the change, confirm that the test passes.
- Use `unittest`, not `pytest`. Tests mirror the source layout under `<package>/test/`.
- Before you report a task as done, run the checks from CONTRIBUTING.md for each package you changed. Report
  failures with their output.
- Install dependencies with `pip`. Keep `uv.lock` out of commits.
- Stage files by explicit path (`git add <path>`) and commit only the files of the task.

## Code conventions
Apply these to new code and to code you change for the task. Leave unrelated code as it is.
- Inline a function that is called from one place only, unless it is longer than about 30 lines or needs its own
  unit test.
- Avoid needless work, e.g. copying a list you only read, or building a list just to iterate over it once.
- Compute values on demand or pass them as arguments instead of storing them as instance attributes.

## AAS specification
- The version of each specification part is in the *Specification Compliance* table of the root
  [README.md](README.md).
- When in doubt, or when you are asked to do something according to the specification, look it up at
  `https://industrialdigitaltwin.io/aas-specifications/{DOC_ID}/{VERSION}/index.html`. Write `{VERSION}` exactly as in the README, e.g. `v3.1`, as `v3.1.0` returns 404.
- `{DOC_ID}`: `IDTA-01001` (Part 1: Metamodel), `IDTA-01002` (Part 2: API), `IDTA-01003-a` / `IDTA-01003-b`
  (Part 3a/3b: Data Specifications), `IDTA-01004` (Part 4: Security), `IDTA-01005` (Part 5: AASX).
- The sources of the specification are published as AsciiDoc in the
  [admin-shell-io](https://github.com/admin-shell-io) GitHub organization, one repository per part
  (e.g. `aas-specs-metamodel`, `aas-specs-api`).
- Back claims about the specification with a link to the exact section (its anchor in the web version).
- Take the JSON and XSD schemas from the release tag of
  [aas-specs-metamodel](https://github.com/admin-shell-io/aas-specs-metamodel), never from `master`.
