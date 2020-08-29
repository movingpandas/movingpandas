# MovingPandas

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![build status](https://travis-ci.com/anitagraser/movingpandas.svg?branch=master)](https://travis-ci.com/anitagraser/movingpandas)
[![docs status](https://readthedocs.org/projects/movingpandas/badge/?version=latest)](https://movingpandas.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/anitagraser/movingpandas/branch/master/graph/badge.svg)](https://codecov.io/gh/anitagraser/movingpandas)
[![DOI](https://zenodo.org/badge/161995245.svg)](https://zenodo.org/badge/latestdoi/161995245)
[![pyOpenSci](https://camo.githubusercontent.com/63ff31cdb80a06361e53ac2b9ac0d184118ebd0b/68747470733a2f2f74696e7975726c2e636f6d2f7932326e62387570)](https://github.com/pyOpenSci/software-review/issues/18)

<img align="right" src="https://anitagraser.github.io/movingpandas/pics/movingpandas.png">

MovingPandas implements a Trajectory class and corresponding methods based on **[GeoPandas](https://geopandas.org)**.

Visit **[movingpandas.org](http://movingpandas.org)** for details! 

You can try MovingPandas in a MyBinder notebook - no installation required: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/anitagraser/movingpandas/binder-tag?filepath=tutorials/0_getting_started.ipynb)


## Documentation

The official documentation is hosted on **[ReadTheDocs](https://movingpandas.readthedocs.io)**


## Examples

![movingpandas_animated](https://user-images.githubusercontent.com/590385/89099729-a9f1da00-d3f1-11ea-91c2-904d477fdcb2.gif)
![movingpandas_ais](https://user-images.githubusercontent.com/590385/73123664-5ad67280-3f92-11ea-8b42-02a0135f0f5c.PNG)

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

### Develop mode

To install MovingPandas in ["develop" or "editable" mode](https://python-packaging-tutorial.readthedocs.io/en/latest/setup_py.html#develop-mode) you may use: 



```
python setup.py develop
```

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

### About MovingPandas

[0] [Graser, A. (2019). MovingPandas: Efficient Structures for Movement Data in Python. GI_Forum ‒ Journal of Geographic Information Science 2019, 1-2019, 54-68. doi:10.1553/giscience2019_01_s54.](https://www.austriaca.at/rootcollection?arp=0x003aba2b)

[1] [Graser, A. & Dragaschnig, M. (2020). Exploring movement data in notebook environments. To be presented at MoVIS 2020, IEEE VIS 2020.](http://move.geog.ucsb.edu/movis2020/)

### Referencing MovingPandas

* [Graser, A. & Dragaschnig, M. (2020). Open Geospatial Tools for Movement Data Exploration. KN ‒ Journal of Cartography and Geographic Information, 70(1), 3-10. doi:10.1007/s42489-020-00039-y.](https://link.springer.com/article/10.1007/s42489-020-00039-y)

### Workshop Videos

* [Graser, A. (2019). Analyzing Movement Data with MovingPandas. Workshop at the OpenGeoHub summer school, Münster, Germany.](http://www.youtube.com/watch?v=qeLQfnpJV1g)

[![WorkshopVideo](https://user-images.githubusercontent.com/590385/67161044-f08cb100-f356-11e9-8799-f972175ec7f4.png)](http://www.youtube.com/watch?v=qeLQfnpJV1g "Anita Graser: Analyzing movement data")
