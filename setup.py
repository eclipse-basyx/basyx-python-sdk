from setuptools import setup, find_packages

# Metadata is now in pyproject.toml, but we need this file for backwards compatibility
setup(
    name="basyx-python-sdk",
    packages=find_packages(exclude=["test", "test.*"]),
    package_data={
        "basyx": ["py.typed"],
        "basyx.aas.examples.data": ["TestFile.pdf"],
    },

)
