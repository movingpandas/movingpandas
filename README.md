# MovingPandas

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![build status](https://travis-ci.com/anitagraser/movingpandas.svg?branch=master)](https://travis-ci.com/anitagraser/movingpandas)
[![docs status](https://readthedocs.org/projects/movingpandas/badge/?version=latest)](https://movingpandas.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/anitagraser/movingpandas/branch/master/graph/badge.svg)](https://codecov.io/gh/anitagraser/movingpandas)
<!--[![pyOpenSci](https://tinyurl.com/y22nb8up)](https://github.com/pyOpenSci/software-review/issues/18)-->


MovingPandas implements a Trajectory class and corresponding methods based on **GeoPandas**.

You can try MovingPandas in a MyBinder notebook - no installation required: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/anitagraser/movingpandas/binder-tag)


## Documentation

The official documentation is hosted on ReadTheDocs: https://movingpandas.readthedocs.io

## Introduction 

Common Simple Features-based data models where trajectories consist of geometries with timestamps can be readily implemented in GIS environments, but they suffer from a lack of support for the temporal dimension, such as functions for duration and speed.

In stark contrast, the Pandas data analysis library has been developed with a strong focus on time series. By choosing Pandas data structures (1D series and 2D DataFrames) as a base for MovingPandas, we gain access to the library’s built-in functionality, including: flexible indexing on timestamps and other column types; memory-efficient sparse data structures for data that is mostly missing or mostly constant; an integrated ‘group by’ engine for aggregating and transforming datasets, and moving window statistics (rolling mean, rolling standard deviation, etc.).

GeoPandas extends the data types that can be used in Pandas DataFrames, thus creating GeoDataFrames. Geometric operations on these spatial data types are performed by Shapely. Geopandas further depends on Fiona for file access (which enables direct reading of GeoDataFrames from common spatial file formats, such as GeoPackage or Shapefile), and descartes and matplotlib for plotting.

MovingPandas uses the following terminology. A *trajectory* is, or more correctly has, a time-ordered series of geometries. These
geometries and associated attributes are stored in a GeoDataFrame *df*. Furthermore, a trajectory can have a *parent* trajectory and can itself be the parent of successive trajectories. Raw unsegmented streams of movement data, as well as semantically meaningful subsections or other subsections, can therefore be represented as trajectories. Depending on the use case, the trajectory object can access a point-based or a line-based representation of its data. (Source: [[0]](#publications))

## Examples

![movingpandas_ais3](https://user-images.githubusercontent.com/590385/73123652-4eeab080-3f92-11ea-9fb3-15afafcdb33f.PNG)
![movingpandas_ais15](https://user-images.githubusercontent.com/590385/73123664-5ad67280-3f92-11ea-8b42-02a0135f0f5c.PNG)

## Installation

MovingPandas for Python >= 3.7 and all it's dependencies are available from [conda-forge](https://anaconda.org/conda-forge/movingpandas): and can be installed using `conda install -c conda-forge movingpandas`.

Note that it is **NOT recommended** to install MovingPandas from [PyPI](https://pypi.org/project/movingpandas/)!
If you're on Windows or Mac, many GeoPandas / MovingPandas dependencies cannot be pip installed 
(for details see the corresponding notes in the [GeoPandas documentation](https://geopandas.readthedocs.io/en/latest/install.html#installing-with-pip)).
On Ubuntu, pip install fails on cartopy with "Proj 4.9.0 must be installed".

## Development Installation 

Use the following steps to run the notebooks using the current development version:

### Using conda

**Linux/Mac**:  

```
conda env create -f environment.yml
```

**Windows**: 

```
conda config --add channels conda-forge
conda config --add channels defaults
conda config --set channel_priority strict
conda env create -f environment.yml
```

*On Windows, because conda-forge relies on some package built with defaults blas (like scipy) one must use the defaults channel on top of conda-forge and activate conda's new strict channel feature.* Source: https://github.com/conda-forge/gdal-feedstock/issues/269#issuecomment-473661530

### Using Anaconda

1. Install Anaconda
2. Clone the movingpandas repository
3. In Anaconda Navigator | Environments | Import select the movingpandas environment.yml from the cloned directory:

![image](https://user-images.githubusercontent.com/590385/62143367-2db14c00-b2f0-11e9-8cb9-fb7993b7f62e.png)

4. Wait until the environment is ready, then change to the Home tab and install Jupyter notebooks into the movingpandas environment
5. Launch Jupyter notebooks and navigate to the `movingpandas/tutorials` directory to execute them
6. Now you can run the notebooks, experiment with the code and adjust it to your own data

Known issues:

* On Windows, importing rasterio can lead to DLL errors. If this happens, downgrade the rasterio version to 1.0.13.

## Contributing to MovingPandas [![GitHub contributors](https://img.shields.io/github/contributors/anitagraser/movingpandas.svg)](https://github.com/anitagraser/movingpandas/graphs/contributors)

All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.

A detailed overview on how to contribute can be found in the [contributing guide](https://github.com/anitagraser/movingpandas/blob/master/CONTRIBUTING.md) on GitHub.

## Related Python Packages

[scikit-mobility](https://github.com/scikit-mobility/scikit-mobility) is a similar package which also deals with movement data. 
It implements TrajectoryDataFrames and FlowDataFrames on top of Pandas instead of GeoPandas. 
There is little overlap in the covered use cases and implemented functionality (comparing 
[MovingPandas tutorials](https://github.com/anitagraser/movingpandas/tree/master/tutorials) and 
[scikit-mobility tutorials](https://github.com/scikit-mobility/scikit-mobility/tree/master/tutorial)). 
MovingPandas focuses on spatio-temporal data exploration with corresponding functions for data manipulation and analysis. 
scikit-mobility on the other hand focuses on computing human mobility metrics, generating synthetic trajectories 
and assessing privacy risks.

## Citation information

Please cite [[0]](#publications) when using MovingPandas in your research.

## Publications

[0] Graser, A. (2019). MovingPandas: Efficient Structures for Movement Data in Python. GI_Forum ‒ Journal of Geographic Information Science 2019, 1-2019, 54-68. doi:10.1553/giscience2019_01_s54. URL: https://www.austriaca.at/rootcollection?arp=0x003aba2b

[1] Graser, A. (2019). Analyzing Movement Data with MovingPandas. Workshop at the OpenGeoHub summer school, Münster, Germany.

[![WorkshopVideo](https://user-images.githubusercontent.com/590385/67161044-f08cb100-f356-11e9-8799-f972175ec7f4.png)](http://www.youtube.com/watch?v=qeLQfnpJV1g "Anita Graser: Analyzing movement data")
