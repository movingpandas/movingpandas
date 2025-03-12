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
[![pyOpenSci](https://tinyurl.com/y22nb8up)](https://github.com/pyOpenSci/software-review/issues/18)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![StandWithUkraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109434720057484377?domain=https%3A%2F%2Ffosstodon.org)](https://fosstodon.org/@movingpandas)

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md)


<img align="right" src="https://movingpandas.github.io/movingpandas/assets/img/movingpandas.png">

MovingPandas is a Python library for movement data exploration and analysis.

MovingPandas provides trajectory data structures and functions for handling movement data based on Pandas, **[GeoPandas](https://geopandas.org)**, and HoloViz.

Visit **[movingpandas.org](http://movingpandas.org)** for details! 

You can run **[MovingPandas examples](https://github.com/movingpandas/movingpandas-examples)** on MyBinder - no installation required: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/movingpandas/movingpandas-examples/main) (These examples use the latest MovingPandas release version.) 

To try the cutting-edge dev version, use [this MyBinder link](https://mybinder.org/v2/gh/movingpandas/movingpandas/main?filepath=tutorials/1-getting-started.ipynb).


## Documentation

We recommend starting your MovingPandas journey with the **[tutorial notebooks on the official homepage](https://movingpandas.org/examples)**

The official API documentation is hosted on **[ReadTheDocs](https://movingpandas.readthedocs.io)**


## Examples


### Trajectory plots 

Create interactive trajectory plots using Folium and Geoviews with ease

![image](https://github.com/user-attachments/assets/a62b3a4e-e5fc-4d96-b67d-e03dff29a20e)


#### Including multiple linked plots  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/2-analysis-examples/bird-migration.html)

![movingpandas_animated](https://user-images.githubusercontent.com/590385/137953765-33f9ce1b-037c-4c86-82b2-0620de5ca28f.gif)


#### For all types of tracking data, e.g. [video-based trajectories](https://anitagraser.com/2023/05/21/analyzing-video-based-bicycle-trajectories/)

![Bicycle tracks from object tracking in videos](https://github.com/movingpandas/movingpandas/assets/590385/c4a0f682-bb94-4b15-ac03-a4d854008937)


#### Including plots in custom projections [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/2-analysis-examples/iceberg.html)

![MovingPandas Iceberg trajectory in custom SouthPolarStereo projection](https://github.com/movingpandas/movingpandas/assets/590385/334304eb-da78-4779-b46b-5492fd54d8ed)


### Stop detection  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/1-tutorials/8-detecting-stops.html)

Detect stops in trajectories, extract them as points or segments, and use them to split trajectories

![movingpandas_stop_detection](https://user-images.githubusercontent.com/590385/236671475-a37aa046-76d6-48b9-ae6d-d1358a591953.png)


### Trajectory generalization  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/1-tutorials/7-generalizing-trajectories.html)

Generalize trajectories using spatial, temporal, and spatiotemporal methods

![movingpandas_generalize](https://user-images.githubusercontent.com/590385/142756559-012a15fe-736c-474c-b244-0ee02090d592.gif)


### Trajectory cleaning & smoothing  [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/1-tutorials/10-smoothing-trajectories.html)

Clean and sooth trajectories by removing outliers and applying Kalman filters

![movingpandas smooth](https://user-images.githubusercontent.com/590385/184359439-52eca394-5df6-40b2-a5b3-54543c3ccf34.png)


### Trajectory aggregation [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-white.svg)](https://movingpandas.github.io/movingpandas-website/1-tutorials/9-aggregating-trajectories.html)

Aggregate trajectories to explore larger patterns

![movingpandas_ais](https://user-images.githubusercontent.com/590385/137953890-d43c7fe5-5aea-4e29-8ce1-f0d529c3220f.png)


## Installation

MovingPandas for Python >= 3.7 and all its dependencies are available from [conda-forge](https://anaconda.org/conda-forge/movingpandas) and can be installed using 

`conda install -c conda-forge movingpandas`
 
 or faster using 
 
 `mamba install -c conda-forge movingpandas`


Note that it is **NOT recommended** to install MovingPandas from [PyPI](https://pypi.org/project/movingpandas/)!
If you are using Windows or Mac, many GeoPandas / MovingPandas dependencies may not install correctly with pip
(for details see the corresponding notes in the [GeoPandas documentation](https://geopandas.readthedocs.io/en/latest/getting_started/install.html)).
On Ubuntu, pip install may fail, e.g. on cartopy with "Proj 4.9.0 must be installed".


## Development installation 

Use the following steps to run the notebooks using the current development version:


### Using conda / mamba

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
	volume = {7},
	number = {1},
	issn = {2308-1708, 2308-1708},
	shorttitle = {{MovingPandas}},
	url = {https://hw.oeaw.ac.at?arp=0x003aba2b},
	doi = {10.1553/giscience2019_01_s54},
	language = {en},
	urldate = {2023-04-19},
	journal = {GI\_Forum ‒ Journal of Geographic Information Science},
	author = {Graser, Anita},
	year = {2019},
	pages = {54--68},
}
```

[1] [Graser, A. & Dragaschnig, M. (2020). Exploring movement data in notebook environments. Presented at MoVIS 2020, IEEE VIS 2020.](http://move.geog.ucsb.edu/wp-content/uploads/2020/10/MoVIS20_paper_4.pdf)

[2] [Graser, A. (2021). Exploratory Movement Data Analysis. GeoPython 2021. – 🎬 video](https://vimeo.com/539472075/bfa7347707)


### Scientific publications using MovingPandas

1. [Graser, A. & Dragaschnig, M. (2020). Open Geospatial Tools for Movement Data Exploration. KN ‒ Journal of Cartography and Geographic Information, 70(1), 3-10. doi:10.1007/s42489-020-00039-y.](https://link.springer.com/article/10.1007/s42489-020-00039-y) - *"For example, Fig. 4 shows how MovingPandas can be used to split a trajectory into subtrajectories and plot the results."*
1. [Kirkland, L. A., de Waal, A., & de Villiers, J. P. (2020). Evaluation of a Pure-Strategy Stackelberg Game for Wildlife Security in a Geospatial Framework. In Southern African Conference for Artificial Intelligence Research (pp. 101-118). Springer, Cham.](https://www.researchgate.net/publication/347786937_Evaluation_of_a_Pure-Strategy_Stackelberg_Game_for_Wildlife_Security_in_a_Geospatial_Framework) - *"The movingpandas Python library [12] is utilised to store trajectories which can be easily analysed and plotted after the simulation."*
1. [Depellegrin, D., Bastianini, M., Fadini, A., & Menegon, S. (2020). The effects of COVID-19 induced lockdown measures on maritime settings of a coastal region. Science of the Total Environment, 740, 140123.](https://doi.org/10.1016/j.scitotenv.2020.140123) - *"We combined the Python libraries scikit-Mobility (Pappalardo et al., 2019) and MovingPandas (Graser, 2019) to pre-process position data received from the AAOT and to reconstruct and represent the vessel trajectory in the lockdown assessment period."*
1. [Graser, A. (2021). An exploratory data analysis protocol for identifying problems in continuous movement data. Journal of Location Based Services. doi:10.1080/17489725.2021.1900612.](https://doi.org/10.1080/17489725.2021.1900612) - MovingPandas is used to plot individual trajectories colored by movement speeed. 
1. [Mehri, S., Alesheikh, A. A., & Basiri, A. (2021). A Contextual Hybrid Model for Vessel Movement Prediction. IEEE Access, 9, 45600-45613.](https://ieeexplore.ieee.org/abstract/document/9380635/) - *"AIS messages are converted into trajectories by a Python library named, MovingPandas"*
1. [Soularidis, A., & Kotis, K. (2022). Semantic Modeling and Reconstruction of Drones’ Trajectories. In European Semantic Web Conference (pp. 158-162). Springer, Cham.](https://2022.eswc-conferences.org/wp-content/uploads/2022/05/pd_Soularidis_et_al_paper_192.pdf) - *"The goal of this paper is to present our position related to the semantic trajectories of swarms of drones, towards proposing methods for extending MovingPandas, a widely used open-source trajectory analytics and visualization tool."*
1. [Elayam, M. M., Ray, C., & Claramunt, C. (2022). A hierarchical graph-based model for mobility data representation and analysis. Data & Knowledge Engineering, 102054.](https://www.sciencedirect.com/science/article/abs/pii/S0169023X22000532) - *"The implementation combines several open source tools such as Python, MovingPandas library, Uber H3 index, Neo4j graph database management system"*
1. [Kotis, K., & Soularidis, A. (2023). ReconTraj4Drones: A Framework for the Reconstruction and Semantic Modeling of UAVs’ Trajectories on MovingPandas. Applied Sciences, 13(1), 670.](https://www.mdpi.com/2076-3417/13/1/670) - *"This framework extends MovingPandas, a widely used and open-source trajectory analytics and visualization tool."*
1. [Šakan, D., Žuškin, S., Rudan, I., & Brčić, D. (2023). Container Ship Fleet Route Evaluation and Similarity Measurement between Two Shipping Line Ports. Journal of Marine Science and Engineering, 11(2), 400.](https://www.mdpi.com/2130602) - *"To create routes, we used the MovingPandas library"* (Horizon Europe project no. 101077026 SafeNav).
1. [Sheehan, C., & Green, T. (2023) ChargeUp! Data Swap!. Using data from battery swapping e-motorcycles in Nairobi to assess impacts and plan infrastructure. Imperial College London. White paper.](https://p4gpartnerships.org/sites/default/files/2023-06/341%20IMP%20Energy%20futures%20ChargeUp_Data%20Swap_White%20paper_AC2.pdf) - *"the raw GPS co-ordinates and their timestamps were processed to detect individual trajectories (trips) for each battery using MovingPandas"*
1. [Gu, C., Liu, L., Zhang, Y., Wei, B., Cui, B., & Gong, D. (2023). Understanding the spatial heterogeneity of grazing pressure in the Three-River-Source Region on the Tibetan Plateau. Journal of Geographical Sciences, 33(8), 1660-1680.](https://link.springer.com/article/10.1007/s11442-023-2147-1) - *"we used MovingPandas, a python package for movement data analysis, to obtain the daily moving distance and home range information"*
1. [Duarte, M. M. G., & Sakr, M. (2023). A Benchmark of Existing Tools for Outlier Detection and Cleaning in Trajectories.](https://www.researchsquare.com/article/rs-3356633/v1) - *"The benchmark includes MovingPandas, Scikit-mobility, Scikit-learn, Ptrail, PyMove, movetk, MEOS, Argosﬁlter, Stmove and MOutlier."* (Horizon Europe project no. 101070279 MobiSpaces). 
1. [Lei, J., Chu, Z., Wu, Y., Liu, X., Luo, M., He, W., & Liu, C. (2024). Predicting vessel arrival times on inland waterways: A tree-based stacking approach. Ocean Engineering, 294, 116838.](https://www.sciencedirect.com/science/article/abs/pii/S0029801824001756) - *"the historical voyages are processed with the movingpandas library and stored as GeoDataFrames"*
1. [Golze, J., & Sester, M. (2024). Determining user specific semantics of locations extracted from trajectory data. Transportation Research Procedia, 78, 215-221.](https://www.sciencedirect.com/science/article/pii/S2352146524000814) - *"stop points are extracted from the GPS trajectories using the Python framework MovingPandas"*
1. [Van Deursen, J., Creany, N., Smith, B., Freimund, W., Avgar, T., & Monz, C. A. (2024). Recreation specialization: Resource selection functions as a predictive tool for protected area recreation management. Applied Geography, 167, 103276.](https://www.sciencedirect.com/science/article/abs/pii/S014362282400081X) - *"GeoPandas and MovingPandas packages in Python were used to analyze the GPS data collected and calculate the thirteen STMs (spatio-temporal metrics)"*
1. [Wicaksono, S. B. (2024). From Data Cleaning to Predictive Models: A Strategic Approach to Analyzing Bus and Ship Trajectories. Master Thesis in Data Science, Department of Mathemetics, University of Padova.](https://thesis.unipd.it/handle/20.500.12608/69505) - *"we utilize the stop detection tools provided by MovingPandas"*
1. [Skåntorp, J., Rolfes, J., Haraldsson, R., Liu, X., Zhao, S., & Rothhämel, M. (2024). Data-driven bicycle driving cycles via mixed-integer programming. 10.13140/RG.2.2.19928.10240](http://dx.doi.org/10.13140/RG.2.2.19928.10240) - *"we utilized the Kalman filter from the MovingPandas library"*
1. [Hoffmann, V., Webert, J. H., Murray, B., & Graf, R. (2024). Data-driven construction of maritime traffic networks for AI-based route prediction. Journal of Physics: Conference Series, 2867.](https://iopscience.iop.org/article/10.1088/1742-6596/2867/1/012048) - *"Messages are converted to trajectories using MovingPandas"* (Horizon 2020 project no. 957237 VesselAI).
1. [Mehri, S., Hooshangi, N., & Mahdizadeh Gharakhanlou, N. (2025). A Novel Context-Aware Douglas–Peucker (CADP) Trajectory Compression Method. ISPRS International Journal of Geo-Information, 14(2), 58.](https://www.mdpi.com/2220-9964/14/2/58) - *"AIS messages are converted into trajectories using a Python library named MovingPandas"*
1. [Elkin-Frankston, S., McIntyre, J., Brunyé, T.T. et al. (2025). Beyond boundaries: a location-based toolkit for quantifying group dynamics in diverse contexts. Cogn. Research 10, 10 (2025).](https://doi.org/10.1186/s41235-025-00617-6) - *"we first segmented time periods when the group was in motion by identifying break periods using the stop detection feature from the MovingPandas Python package"*
1. [Koszewski, K., Olszewski, R., Pałka, P. et al. (2025). Utilizing IoT Sensors and Spatial Data Mining for Analysis of Urban Space Actors’ Behavior in University Campus Space Design. Sensors, 25(5), 1393.](https://doi.org/10.3390/s25051393) - *"trajectories were processed by the MovingPandas Python library, which offers several valuable processing algorithms, like calculation of velocity, direction of movement, intersections, as well as enabling easy data exchange with other GIS tools using built-in exporters" & "One useful solution turned out to be the MovingPandas’ built-in TrajectoryStopDetector"*
2. [Garcez Duarte, M. M., & Sakr, M. (2025). An experimental study of existing tools for outlier detection and cleaning in trajectories. GeoInformatica, 29(1), 31-51.](https://doi.org/10.1007/s10707-024-00522-y) - *"MovingPandas uses the Kalman Filter (KF) algorithm for outlier detection"*

[Full Google Scholar list](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=10366998261774464895)

### Platforms using MovingPandas

* [MoveApps](https://www.moveapps.org) the free analysis platform for animal tracking data hosted by the Max Planck Institute of Animal Behavior uses MovingPandas TrajectoryCollections as their [default Python IO type](https://docs.moveapps.org/#/create_py_app?id=io-types).
* [AIT Mobility Observation Box](https://www.ait.ac.at/en/solutions/traffic-safety/safe/mobility-observation-box/) uses MovingPandas for processing video-based trajectories 


### Teaching materials referencing MovingPandas

* [Aalto University. Spatial data science for sustainable development course](https://sustainability-gis.readthedocs.io/en/latest/lessons/L3/mobility-analytics.html)
* [University of Trento. Geospatial Analysis and Representation for Data Science course for the master in Data Science](https://napo.github.io/geospatial_course_unitn/lessons/06-mobilty-analytics)

### Workshop videos

* [Graser, A. (2019). Analyzing Movement Data with MovingPandas. Workshop at the OpenGeoHub summer school, Münster, Germany.](http://www.youtube.com/watch?v=qeLQfnpJV1g)
* [Graser, A. (2023). Data Engineering for Mobility Data Science. Workshop at the OpenGeoHub summer school, Poznan, Poland.](https://youtu.be/roPF1oth2Pk)
  
[![WorkshopVideo](https://user-images.githubusercontent.com/590385/67161044-f08cb100-f356-11e9-8799-f972175ec7f4.png)](http://www.youtube.com/watch?v=qeLQfnpJV1g "Anita Graser: Analyzing movement data")
[![ogh2023](https://github-production-user-asset-6210df.s3.amazonaws.com/590385/273573344-5aff5369-3db4-4d9e-9758-c9efccfd29a5.png)](https://youtu.be/roPF1oth2Pk)
