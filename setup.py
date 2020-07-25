import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

# Packages that MovingPandas uses explicitly:
INSTALL_REQUIRES = ['numpy', 'matplotlib', 'shapely', 'pandas', 'geopandas', 'hvplot', 'bokeh', 'cartopy', 'geoviews', 'pyproj']

setuptools.setup(
    name="movingpandas",
    version="0.4.rc1",
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
    install_requires=INSTALL_REQUIRES
)
