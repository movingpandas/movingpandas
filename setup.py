import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

# Packages that MovingPandas uses explicitly:
INSTALL_REQUIRES = [
    'numpy', 'matplotlib', 'shapely<1.8',  # Geoviews is not yet compatible with shapely-1.8.0 https://github.com/holoviz/geoviews/issues/533
    'pandas', 'geopandas', 'hvplot', 'bokeh', 'cartopy', 'geoviews', 'pyproj', 'geopy']

setuptools.setup(
    name="movingpandas",
    version="0.8.rc1",
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
        'smoothing': ['stonesoup']
    }

)
