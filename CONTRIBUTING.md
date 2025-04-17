# Contributing Guide

Thank you for investing your time in contributing to the Eclipse-BaSyx-Python SDK!

In this guide you will get an overview of the contribution workflow from opening an
issue, creating a PR, reviewing, and merging the PR.

Furthermore, it gives some guidelines on how to write commit and pull
request messages, as well as on codestyle and testing.

## Issues

In order to open an issue, go
to https://github.com/eclipse-basyx/basyx-python-sdk/issues and click "**New Issue**".

The first step for a good issue is a descriptive title. The title is a brief description
of the issue, ideally 72 characters or fewer using imperative language.
Furthermore, if you know which module is the cause of your issue, please mention 
it at the beginning of the issue title.

Here are some example for a good title:

```
model.datatypes: Missing type `xs:someThingMadeUp`
compliance_tool: Fail to check aasx package without thumbnail
adapter.aasx: `Property.value` `0` are converted into `NoneType`
```

As you can see, inline code blocks (the backticks) are used to highlight 
class names or types.

In the issue message, use full text or bullet points to describe your issue in detail.
Please include a short paragraph on each of

- Expected behavior:  A description of what the expected behavior should be, so that
  maintainers can understand how the issue differs from the intended functionality.
- Actual behavior: A description of what is actually happening, which can help pinpoint
  the cause of the issue.
- Environment: Information about the operating system, the SDK version used, the version
  of the specification used, or other relevant technical details that may be
  contributing to the issue.

Additionally, if you have ideas on how to address the issue, please include them here!

## Contribute Changes

Here's the standard workflow to contribute changes to Eclipse-BaSyx-Python.

Before contributing, please make sure, you fill out
the [Eclipse Contributor Agreement (ECA)](https://www.eclipse.org/legal/ECA.php). This
is done by creating an Eclipse account for your git e-mail address and then submitting
the following
form: [https://accounts.eclipse.org/user/eca](https://accounts.eclipse.org/user/eca).
The E-Mail address used to sign the ECA is the same one that needs to be used for
committing.

After this, the workflow to submit contributions to Eclipse-BaSyx-Python is pretty
standard, as the picture (based
on [this blog-post by Tomas Beuzen](https://www.tomasbeuzen.com/post/git-fork-branch-pull/))
below shows:

![CONTRIBUTING_Workflow](./etc/CONTRIBUTING_Workflow.png)

1. Fork the Eclipse-BaSyx Repository
2. Clone your fork to your development machine and add Eclipse-BaSyx as `upstream`:

```bash
git remote add upstream https://github.com/eclipse-basyx/basyx-python-sdk
```

3. Pull the branch you want to contribute to:

```bash
git pull upstream <branch_name>
```

Now, you can create a new local branch in which you can create your changes and actually
do your changes. When you're done with that, continue with:

4. Push the new branch to your fork:

```bash
git push origin <your_new_branch>
```

5. Create a [Pull Request](https://github.com/eclipse-basyx/basyx-python-sdk/pulls) from
   your fork `<your_new_branch>` to the Eclipse-BaSyx-Python `<branch_name>`

The Eclipse-BaSyx-Python maintainers will then review the pull request and communicate
the further steps via the comments.

## Commit and Pull Request Messages

In order to effectively communicate, there are some conventions to respect when writing
commit messages and pull requests.

Similarly to when creating an issue, the commit title, as well as the PR title should 
be as short as possible, ideally 72 characters or fewer using imperative language.
If a specific module is affected, please mention it at the beginning of the title.

Here are some examples:

```
model.datatypes: Add type `xs:someThingMadeUp`
compliance_tool: Fix fail to check aasx package without thumbnail
adapter.aasx: Fix `Property.value` `0` converted into `NoneType`
```

The following guidelines are for the commit or PR message text:

- No imperative, full text, bullet points where necessary
- Max. 72 characters per line
- There should be always 2 things in a Commit/PR message:
    - Currently, the situation is this
    - Motivate, why is it now different?
- Don't describe what has been done, as this can be looked up in the code
- Write as long as necessary, as short as possible
- Where sensible, reference the specification, ideally
  via `https://link/to.pdf#Page=123`
- Optionally, where applicable reference respective issues: `Fixes #123`

## Code Quality

The Eclipse BaSyx Python project emphasizes high code quality.
To achieve this, we apply best practices where possible and have developed an extensive suite of tests that are 
expected to pass for each Pull Request to the project. 

### Codestyle
Our code follows the [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
with the following exceptions:
- Line length is allowed to be up to 120 characters, though lines up to 100 characters are preferred.

Additionally, we use [PEP 484 -- Type Hints](https://www.python.org/dev/peps/pep-0484/) throughout the code to enable type checking the code.

Before submitting any changes to the SDK, make sure to let `mypy` and `pycodestyle` check your code and run the unit 
tests with Python's builtin `unittest`. 

### Testing
There are many automated checks implemented in the CI pipelines of this project, all of which are expected to pass 
before new code can be added:

- We check that the Python packages can be built.
- We run the developed unittests and aim for a code coverage of at least 80%.
- We perform static code analysis for type-checking and codestyle, not just in the code itself, but also in codeblocks 
  that are inside docstrings and the `README.md`.
- We check that the automatically generated developer documentation compiles.
- We check that the Python Versions we support match between the different subprojects in the monorepository and are 
  not End of Life.
- We check that the year in the copyright headers in each file (stemming from the license) is correct.

> [!note]
> We strongly suggest to run the tests locally, before submitting a Pull Request, in order to accelerate the review 
> process. 

### Testing the SDK
For testing the SDK locally on your machine, you can install the required tools like so:
```bash
pip install .[dev]
```

> [!note]
> The `.` denotes the current directory and needs to be the directory the `pyproject.toml` is located in.
> Therefore, you need to run this command and the ones below in the `/sdk` directory (relative to the repository root).

Running all checks:
```bash
mypy basyx test
pycodestyle --max-line-length 120 basyx test
python -m unittest
coverage run --source basyx --branch -m unittest
coverage report -m
```

We aim to cover our code with tests by at least 80%.

This should help you sort out the most important bugs in your code.
Note that there are more checks that run in the CI once you open a Pull Request.
If you want to run the additional checks, please refer to the [CI definition](./.github/workflows/ci.yml).

### Testing the Server
Currently, the automated server tests are still under development. 
To test that the server is working, we expect to at least be able to build the docker images and run a container
of it without error. 

For that, you need to have Docker installed on your system. 
In the directory with the `Dockerfile`: 
```bash
docker build -t basyx-python-server .
docker run --name basyx-python-server basyx-python-server
```
Wait until you see the line:
```
INFO success: quit_on_failure entered RUNNING state
```

### Testing the Compliance Tool
For the Compliance Tool, you can install the required tools like this (from the `./compliance_tool` directory):
```bash
pip install -e ../sdk[dev]
pip install .[dev]
```
The first line installs the SDK and its dependencies, the second the developer dependencies for the compliance tool
itself.

Then you can run the checks via:
```bash
mypy basyx test
pycodestyle --max-line-length 120 basyx test
python -m unittest
coverage run --source basyx --branch -m unittest
coverage report -m
```

We aim to cover our code with tests by at least 80%.
This should help you sort out the most important bugs in your code.
Note that there are more checks that run in the CI once you open a Pull Request.
If you want to run the additional checks, please refer to the [CI definition](./.github/workflows/ci.yml).
