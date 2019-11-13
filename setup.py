import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aas",
    version="0.0.1",
    author="Chair of Process Control Engineering, RWTH Aachen",
    author_email="m.thies@plt.rwth-aachen.de",
    description="An implementation of the Asset Administration Shell for Industry 4.0 systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.rwth-aachen.de/acplt/pyaas",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
