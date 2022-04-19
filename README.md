# MovingPandas

[![pypi](https://img.shields.io/pypi/v/movingpandas.svg)](https://pypi.python.org/pypi/movingpandas/)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Tests](https://github.com/anitagraser/movingpandas/actions/workflows/tests.yaml/badge.svg)](https://github.com/anitagraser/movingpandas/actions/workflows/tests.yaml)
[![docs status](https://readthedocs.org/projects/movingpandas/badge/?version=master)](https://movingpandas.readthedocs.io/en/master/)
[![codecov](https://codecov.io/gh/anitagraser/movingpandas/branch/master/graph/badge.svg)](https://codecov.io/gh/anitagraser/movingpandas)
[![DOI](https://zenodo.org/badge/161995245.svg)](https://zenodo.org/badge/latestdoi/161995245)
[![pyOpenSci](https://camo.githubusercontent.com/63ff31cdb80a06361e53ac2b9ac0d184118ebd0b/68747470733a2f2f74696e7975726c2e636f6d2f7932326e62387570)](https://github.com/pyOpenSci/software-review/issues/18)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![StandWithUkraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)


[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)


<img align="right" src="https://anitagraser.github.io/movingpandas/assets/img/movingpandas.png">

MovingPandas implements a Trajectory class and corresponding methods based on **[GeoPandas](https://geopandas.org)**.

Visit **[movingpandas.org](http://movingpandas.org)** for details! 

You can run **[MovingPandas examples](https://github.com/anitagraser/movingpandas-examples)** on MyBinder - no installation required: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/anitagraser/movingpandas-examples/main) (These examples use the latest MovingPandas release version.) 

To try the cutting-edge dev version, use [this MyBinder link](https://mybinder.org/v2/gh/anitagraser/movingpandas/master?filepath=tutorials/1-getting-started.ipynb).

## Documentation

The official documentation is hosted on **[ReadTheDocs](https://movingpandas.readthedocs.io)**

## Examples

### Trajectory plots

![movingpandas_animated](https://user-images.githubusercontent.com/590385/137953765-33f9ce1b-037c-4c86-82b2-0620de5ca28f.gif)

### Stop detection

![movingpandas_stop_detection](https://user-images.githubusercontent.com/590385/137953859-3df81568-eda8-4443-96b8-e82e15c03653.png)

### Trajectory generalization

![movingpandas_generalize](https://user-images.githubusercontent.com/590385/142756559-012a15fe-736c-474c-b244-0ee02090d592.gif)

### Trajectory aggregation

![movingpandas_ais](https://user-images.githubusercontent.com/590385/137953890-d43c7fe5-5aea-4e29-8ce1-f0d529c3220f.png)

## Installation

MovingPandas for Python >= 3.7 and all it's dependencies are available from [conda-forge](https://anaconda.org/conda-forge/movingpandas) and can be installed using `conda install -c conda-forge movingpandas`.

**Conda status**

[![Conda Recipe](https://img.shields.io/badge/recipe-movingpandas-green.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas)

Note that it is **NOT recommended** to install MovingPandas from [PyPI](https://pypi.org/project/movingpandas/)!
If you're on Windows or Mac, many GeoPandas / MovingPandas dependencies cannot be pip installed 
(for details see the corresponding notes in the [GeoPandas documentation](https://geopandas.readthedocs.io/en/latest/getting_started/install.html)).
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

**For a more comprehensive list, including non-Python solutions, check https://github.com/anitagraser/movement-analysis-tools**

[scikit-mobility](https://github.com/scikit-mobility/scikit-mobility) is a similar package which also deals with movement data. 
It implements TrajectoryDataFrames and FlowDataFrames on top of Pandas instead of GeoPandas. 
There is little overlap in the covered use cases and implemented functionality (comparing 
[MovingPandas tutorials](https://github.com/anitagraser/movingpandas/tree/master/tutorials) and 
[scikit-mobility tutorials](https://github.com/scikit-mobility/tutorials)). 
MovingPandas focuses on spatio-temporal data exploration with corresponding functions for data manipulation and analysis. 
scikit-mobility on the other hand focuses on computing human mobility metrics, generating synthetic trajectories 
and assessing privacy risks. Plotting is based on Folium. 

[Traja](https://github.com/traja-team/traja) extends the capabilitis of Pandas DataFrames specific for animal trajectory analysis in 2D. Plots (static) are based on seaborn. 

[PyMove](https://github.com/InsightLab/PyMove) provides functionality similar to MovingPandas. 
It implements PandasMoveDataFrames and DaskMoveDataFrame on top of Pandas and Dask DataFrames. Plotting is based on Folium. 

[Tracktable](https://github.com/sandialabs/tracktable) is a related Python package with its core data structures and algorithms implemented in C++, i.e. it is not based on Pandas. Plotting is based on Cartopy (for still images) and Folium (for interactive rendering).

## Citation information

Please cite [[0]](#publications) when using MovingPandas in your research and reference the appropriate release version. All releases of MovingPandas are listed on [Zenodo](https://doi.org/10.5281/zenodo.3710950) where you will find citation information, including DOIs.  

## Publications

### About MovingPandas

[0] [Graser, A. (2019). MovingPandas: Efficient Structures for Movement Data in Python. GI_Forum ‒ Journal of Geographic Information Science 2019, 1-2019, 54-68. doi:10.1553/giscience2019_01_s54.](https://www.austriaca.at/rootcollection?arp=0x003aba2b)

[1] [Graser, A. & Dragaschnig, M. (2020). Exploring movement data in notebook environments. Presented at MoVIS 2020, IEEE VIS 2020.](http://move.geog.ucsb.edu/wp-content/uploads/2020/10/MoVIS20_paper_4.pdf)

[2] [Graser, A. (2021). Exploratory Movement Data Analysis. GeoPython 2021. – 🎬 video](https://vimeo.com/539472075/bfa7347707)

### Scientific Publications Referencing MovingPandas

* [Pappalardo, L., Simini, F., Barlacchi, G., & Pellungrini, R. (2019). scikit-mobility: A Python library for the analysis, generation and risk assessment of mobility data. arXiv preprint arXiv:1907.07062.](https://arxiv.org/abs/1907.07062)
* [Graser, A. & Dragaschnig, M. (2020). Open Geospatial Tools for Movement Data Exploration. KN ‒ Journal of Cartography and Geographic Information, 70(1), 3-10. doi:10.1007/s42489-020-00039-y.](https://link.springer.com/article/10.1007/s42489-020-00039-y)
* [Kirkland, L. A., de Waal, A., & de Villiers, J. P. (2020). Evaluation of a Pure-Strategy Stackelberg Game for Wildlife Security in a Geospatial Framework. In Southern African Conference for Artificial Intelligence Research (pp. 101-118). Springer, Cham.](https://link.springer.com/chapter/10.1007/978-3-030-66151-9_7)
* [Depellegrin, D., Bastianini, M., Fadini, A., & Menegon, S. (2020). The effects of COVID-19 induced lockdown measures on maritime settings of a coastal region. Science of the Total Environment, 740, 140123.](https://doi.org/10.1016/j.scitotenv.2020.140123)
* [Graser, A. (2021). An exploratory data analysis protocol for identifying problems in continuous movement data. Journal of Location Based Services. doi:10.1080/17489725.2021.1900612.](https://doi.org/10.1080/17489725.2021.1900612)
* [Mehri, S., Alesheikh, A. A., & Basiri, A. (2021). A Contextual Hybrid Model for Vessel Movement Prediction. IEEE Access, 9, 45600-45613.](https://ieeexplore.ieee.org/abstract/document/9380635/)

[Full Google Scholar list](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=10366998261774464895)

### Teaching Material Referencing MovingPandas

* [Aalto University. Spatial data science for sustainable development course](https://sustainability-gis.readthedocs.io/en/latest/lessons/L3/mobility-analytics.html)

### Workshop Videos

* [Graser, A. (2019). Analyzing Movement Data with MovingPandas. Workshop at the OpenGeoHub summer school, Münster, Germany.](http://www.youtube.com/watch?v=qeLQfnpJV1g)

[![WorkshopVideo](https://user-images.githubusercontent.com/590385/67161044-f08cb100-f356-11e9-8799-f972175ec7f4.png)](http://www.youtube.com/watch?v=qeLQfnpJV1g "Anita Graser: Analyzing movement data")
