import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()


def parse_requirements(path):
    """
    Parse requirements files to allow easier separation in to groups.

    Keep the line filtering simple, but we could go the whole way in implementing
    https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
    if required.
    """
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('-r'): # looking at another requirements file
            yield from parse_requirements(line[2:].strip())
        else:
            yield line


# Packages that MovingPandas uses explicitly:
INSTALL_REQUIRES = list(parse_requirements('requirements.txt'))
VIZ_INSTALL_REQUIRES = list(parse_requirements('viz-requirements.txt'))
DEV_INSTALL_REQUIRES = list(parse_requirements('dev-requirements.txt'))


setuptools.setup(
    name="movingpandas",
    version="0.5.rc1",
    author="Anita Graser",
    author_email="anitagraser@gmx.at",
    description="Implementation of Trajectory classes and functions built on top of GeoPandas",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/anitagraser/movingpandas",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'viz': VIZ_INSTALL_REQUIRES,
        'dev': DEV_INSTALL_REQUIRES
    }
)
