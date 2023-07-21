# MovingPandas

[![pypi](https://img.shields.io/pypi/v/movingpandas.svg)](https://pypi.python.org/pypi/movingpandas/)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Recipe](https://img.shields.io/badge/recipe-movingpandas-green.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Tests](https://github.com/movingpandas/movingpandas/actions/workflows/tests.yaml/badge.svg)](https://github.com/movingpandas/movingpandas/actions/workflows/tests.yaml)
[![docs status](https://readthedocs.org/projects/movingpandas/badge/?version=main)](https://movingpandas.readthedocs.io/en/main/)
[![codecov](https://codecov.io/gh/movingpandas/movingpandas/branch/main/graph/badge.svg)](https://codecov.io/gh/movingpandas/movingpandas)
[![DOI](https://zenodo.org/badge/161995245.svg)](https://zenodo.org/badge/latestdoi/161995245)
[![pyOpenSci](https://camo.githubusercontent.com/63ff31cdb80a06361e53ac2b9ac0d184118ebd0b/68747470733a2f2f74696e7975726c2e636f6d2f7932326e62387570)](https://github.com/pyOpenSci/software-review/issues/18)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![StandWithUkraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)

[![Twitter Follow](https://img.shields.io/twitter/follow/MovingPandasOrg)](https://twitter.com/MovingPandasOrg)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109434720057484377?domain=https%3A%2F%2Ffosstodon.org)](https://fosstodon.org/@movingpandas)

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)


<img align="right" src="https://movingpandas.github.io/movingpandas/assets/img/movingpandas.png">

MovingPandas implements a Trajectory class and corresponding methods based on **[GeoPandas](https://geopandas.org)**.

Visit **[movingpandas.org](http://movingpandas.org)** for details! 

You can run **[MovingPandas examples](https://github.com/movingpandas/movingpandas-examples)** on MyBinder - no installation required: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/movingpandas/movingpandas-examples/main) (These examples use the latest MovingPandas release version.) 

To try the cutting-edge dev version, use [this MyBinder link](https://mybinder.org/v2/gh/movingpandas/movingpandas/main?filepath=tutorials/1-getting-started.ipynb).


## Documentation

We recommend starting your MovingPandas journey with the **[tutorial notebooks on the official homepage](https://movingpandas.org/examples)**

The official API documentation is hosted on **[ReadTheDocs](https://movingpandas.readthedocs.io)**


## Examples



### Trajectory plots [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/2-analysis-examples/bird-migration.ipynb)

Create interactive trajectory plots, including multiple linked plots with ease

![movingpandas_animated](https://user-images.githubusercontent.com/590385/137953765-33f9ce1b-037c-4c86-82b2-0620de5ca28f.gif)


#### For all types of tracking data, e.g. [video-based trajectories](https://anitagraser.com/2023/05/21/analyzing-video-based-bicycle-trajectories/)

![Bicycle tracks from object tracking in videos](https://github.com/movingpandas/movingpandas/assets/590385/c4a0f682-bb94-4b15-ac03-a4d854008937)


#### Including plots in custom projections [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/2-analysis-examples/iceberg.ipynb)

![MovingPandas Iceberg trajectory in custom SouthPolarStereo projection](https://github.com/movingpandas/movingpandas/assets/590385/334304eb-da78-4779-b46b-5492fd54d8ed)


### Stop detection  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/1-tutorials/8-detecting-stops.ipynb)

Detect stops in trajectories, extract them as points or segments, and use them to split trajectories

![movingpandas_stop_detection](https://user-images.githubusercontent.com/590385/236671475-a37aa046-76d6-48b9-ae6d-d1358a591953.png)


### Trajectory generalization  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/1-tutorials/7-generalizing-trajectories.ipynb)

Generalize trajectories using spatial, temporal, and spatiotemporal methods

![movingpandas_generalize](https://user-images.githubusercontent.com/590385/142756559-012a15fe-736c-474c-b244-0ee02090d592.gif)


### Trajectory cleaning & smoothing  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/1-tutorials/10-smoothing-trajectories.ipynb)

Clean and sooth trajectories by removing outliers and applying Kalman filters

![movingpandas smooth](https://user-images.githubusercontent.com/590385/184359439-52eca394-5df6-40b2-a5b3-54543c3ccf34.png)


### Trajectory aggregation [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/1-tutorials/9-aggregating-trajectories.ipynb)

Aggregate trajectories to explore larger patterns

![movingpandas_ais](https://user-images.githubusercontent.com/590385/137953890-d43c7fe5-5aea-4e29-8ce1-f0d529c3220f.png)


## Installation

MovingPandas for Python >= 3.7 and all it's dependencies are available from [conda-forge](https://anaconda.org/conda-forge/movingpandas) and can be installed using 

`conda install -c conda-forge movingpandas`
 
 or faster using 
 
 `mamba install -c conda-forge movingpandas`


Note that it is **NOT recommended** to install MovingPandas from [PyPI](https://pypi.org/project/movingpandas/)!
If you're on Windows or Mac, many GeoPandas / MovingPandas dependencies cannot be pip installed 
(for details see the corresponding notes in the [GeoPandas documentation](https://geopandas.readthedocs.io/en/latest/getting_started/install.html)).
On Ubuntu, pip install fails on cartopy with "Proj 4.9.0 must be installed".


## Development installation 

Use the following steps to run the notebooks using the current development version:


### Using conda

```
conda env create -f environment.yml
```

### Develop mode

To install MovingPandas in ["develop" or "editable" mode](https://python-packaging-tutorial.readthedocs.io/en/latest/setup_py.html#develop-mode) you may use: 

```
python setup.py develop
```


## Contributing to MovingPandas [![GitHub contributors](https://img.shields.io/github/contributors/movingpandas/movingpandas.svg)](https://github.com/movingpandas/movingpandas/graphs/contributors)

All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.

A detailed overview on how to contribute can be found in the [contributing guide](https://github.com/movingpandas/movingpandas/blob/main/CONTRIBUTING.md) on GitHub.


## Related Python packages

**For a more comprehensive list, including non-Python solutions, check https://github.com/anitagraser/movement-analysis-tools**

[scikit-mobility](https://github.com/scikit-mobility/scikit-mobility) is a similar package which also deals with movement data. 
It implements TrajectoryDataFrames and FlowDataFrames on top of Pandas instead of GeoPandas. 
There is little overlap in the covered use cases and implemented functionality (comparing 
[MovingPandas tutorials](https://github.com/movingpandas/movingpandas/tree/main/tutorials) and 
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

```
@article{graser_movingpandas_2019,
	title = {{MovingPandas}: {Efficient} {Structures} for {Movement} {Data} in {Python}},
	volume = {1},
	issn = {2308-1708, 2308-1708},
	shorttitle = {{MovingPandas}},
	url = {https://hw.oeaw.ac.at?arp=0x003aba2b},
	doi = {10.1553/giscience2019_01_s54},
	language = {en},
	urldate = {2023-04-19},
	journal = {GI\_Forum},
	author = {Graser, Anita},
	year = {2019},
	pages = {54--68},
}
```

[1] [Graser, A. & Dragaschnig, M. (2020). Exploring movement data in notebook environments. Presented at MoVIS 2020, IEEE VIS 2020.](http://move.geog.ucsb.edu/wp-content/uploads/2020/10/MoVIS20_paper_4.pdf)

[2] [Graser, A. (2021). Exploratory Movement Data Analysis. GeoPython 2021. – 🎬 video](https://vimeo.com/539472075/bfa7347707)


### Scientific publications using MovingPandas

* [Graser, A. & Dragaschnig, M. (2020). Open Geospatial Tools for Movement Data Exploration. KN ‒ Journal of Cartography and Geographic Information, 70(1), 3-10. doi:10.1007/s42489-020-00039-y.](https://link.springer.com/article/10.1007/s42489-020-00039-y) - *"For example, Fig. 4 shows how MovingPandas can be used to split a trajectory into subtrajectories and plot the results."*
* [Kirkland, L. A., de Waal, A., & de Villiers, J. P. (2020). Evaluation of a Pure-Strategy Stackelberg Game for Wildlife Security in a Geospatial Framework. In Southern African Conference for Artificial Intelligence Research (pp. 101-118). Springer, Cham.](https://www.researchgate.net/publication/347786937_Evaluation_of_a_Pure-Strategy_Stackelberg_Game_for_Wildlife_Security_in_a_Geospatial_Framework) - *"The movingpandas Python library [12] is utilised to store trajectories which can be easily analysed
and plotted after the simulation."*
* [Depellegrin, D., Bastianini, M., Fadini, A., & Menegon, S. (2020). The effects of COVID-19 induced lockdown measures on maritime settings of a coastal region. Science of the Total Environment, 740, 140123.](https://doi.org/10.1016/j.scitotenv.2020.140123) - *"We combined the Python libraries scikit-Mobility (Pappalardo et al., 2019) and MovingPandas (Graser, 2019) to pre-process position data received from the AAOT and to reconstruct and represent the vessel trajectory in the lockdown assessment period."*
* [Graser, A. (2021). An exploratory data analysis protocol for identifying problems in continuous movement data. Journal of Location Based Services. doi:10.1080/17489725.2021.1900612.](https://doi.org/10.1080/17489725.2021.1900612) - MovingPandas is used to plot individual trajectories colored by movement speeed. 
* [Mehri, S., Alesheikh, A. A., & Basiri, A. (2021). A Contextual Hybrid Model for Vessel Movement Prediction. IEEE Access, 9, 45600-45613.](https://ieeexplore.ieee.org/abstract/document/9380635/) - *"AIS messages are converted into trajectories by a Python library named, MovingPandas"*
* [Soularidis, A., & Kotis, K. (2022). Semantic Modeling and Reconstruction of Drones’ Trajectories. In European Semantic Web Conference (pp. 158-162). Springer, Cham.](https://2022.eswc-conferences.org/wp-content/uploads/2022/05/pd_Soularidis_et_al_paper_192.pdf) - *"The goal of this paper is to present our position related to the semantic trajectories of swarms of drones, towards proposing methods for extending MovingPandas, a widely used open-source trajectory analytics and visualization tool."*
* [Elayam, M. M., Ray, C., & Claramunt, C. (2022). A hierarchical graph-based model for mobility data representation and analysis. Data & Knowledge Engineering, 102054.](https://www.sciencedirect.com/science/article/abs/pii/S0169023X22000532) - *"The implementation combines several open source tools such as Python, MovingPandas library, Uber H3 index, Neo4j graph database management system ..."*
* [Kotis, K., & Soularidis, A. (2023). ReconTraj4Drones: A Framework for the Reconstruction and Semantic Modeling of UAVs’ Trajectories on MovingPandas. Applied Sciences, 13(1), 670.](https://www.mdpi.com/2076-3417/13/1/670) - *"This framework extends MovingPandas, a widely used and open-source trajectory analytics and visualization tool."*
* [Šakan, D., Žuškin, S., Rudan, I., & Brčić, D. (2023). Container Ship Fleet Route Evaluation and Similarity Measurement between Two Shipping Line Ports. Journal of Marine Science and Engineering, 11(2), 400.](https://www.mdpi.com/2130602) - *"To create routes, we used the MovingPandas library ..."* (Horizon Europe project no. 101077026 SafeNav).
* [Sheehan, C., & Green, T. (2023) ChargeUp! Data Swap!. Using data from battery swapping e-motorcycles in Nairobi to assess impacts and plan infrastructure. Imperial College London. White paper.](https://p4gpartnerships.org/sites/default/files/2023-06/341%20IMP%20Energy%20futures%20ChargeUp_Data%20Swap_White%20paper_AC2.pdf) - *"the raw GPS co-ordinates and their timestamps were processed to detect individual trajectories (trips) for each battery using MovingPandas"*

[Full Google Scholar list](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=10366998261774464895)


### Teaching materials referencing MovingPandas

* [Aalto University. Spatial data science for sustainable development course](https://sustainability-gis.readthedocs.io/en/latest/lessons/L3/mobility-analytics.html)
* [University of Trento. Geospatial Analysis and Representation for Data Science course for the master in Data Science](https://napo.github.io/geospatial_course_unitn/lessons/06-mobilty-analytics)

### Workshop videos

* [Graser, A. (2019). Analyzing Movement Data with MovingPandas. Workshop at the OpenGeoHub summer school, Münster, Germany.](http://www.youtube.com/watch?v=qeLQfnpJV1g)

[![WorkshopVideo](https://user-images.githubusercontent.com/590385/67161044-f08cb100-f356-11e9-8799-f972175ec7f4.png)](http://www.youtube.com/watch?v=qeLQfnpJV1g "Anita Graser: Analyzing movement data")
