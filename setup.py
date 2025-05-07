import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = (
        "Trajectory data structures and functions for handling movement data"
    )

# Packages that MovingPandas uses explicitly:
INSTALL_REQUIRES = [
    "matplotlib",
    "geopandas",
    "geopy",
]

setuptools.setup(
    name="movingpandas",
    version="0.22.0",
    author="Anita Graser",
    author_email="anitagraser@gmx.at",
    description="MovingPandas provides trajectory data structures and "
    "functions for handling movement data based on Pandas, GeoPandas, and more. "
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
