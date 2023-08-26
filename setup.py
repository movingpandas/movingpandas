import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

# Packages that MovingPandas uses explicitly:
INSTALL_REQUIRES = [
    "matplotlib",
    "geopandas",
    "fiona",
    "rtree",
    "geopy",
]

setuptools.setup(
    name="movingpandas",
    version="0.17.1",
    author="Anita Graser",
    author_email="anitagraser@gmx.at",
    description="MovingPandas implements Trajectory classes and corresponding methods "
    "for the analysis of movement data based on GeoPandas. "
    "Visit movingpandas.org for details.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/movingpandas/movingpandas",
    packages=[
        "movingpandas",
        "movingpandas.tools",
        "movingpandas.tests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "smoothing": ["stonesoup"],
        "viz": ["hvplot", "bokeh", "cartopy", "geoviews"],
    },
)
