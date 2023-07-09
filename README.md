<img  width="50%" src="https://movingpandas.github.io/movingpandas/assets/img/logo-wide.svg">

MovingPandas is a Python library for handling movement data based on Pandas, [GeoPandas](https://geopandas.org), and [HoloViz](https://holoviz.org). 

MovingPandas provides trajectory data structures and functions for movement data exploration and analysis.

The official MovingPandas API documentation is hosted on [ReadTheDocs](https://movingpandas.readthedocs.io).

For more information about individual releases, check out the [Changelog](https://github.com/movingpandas/movingpandas/releases).

[![Twitter Follow](https://img.shields.io/twitter/follow/MovingPandasOrg)](https://twitter.com/MovingPandasOrg)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109434720057484377?domain=https%3A%2F%2Ffosstodon.org)](https://fosstodon.org/@movingpandas)

[![docs status](https://readthedocs.org/projects/movingpandas/badge/?version=main)](https://movingpandas.readthedocs.io/en/main/)
[![pyOpenSci](https://camo.githubusercontent.com/63ff31cdb80a06361e53ac2b9ac0d184118ebd0b/68747470733a2f2f74696e7975726c2e636f6d2f7932326e62387570)](https://github.com/pyOpenSci/software-review/issues/18)
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/movingpandas.svg)](https://anaconda.org/conda-forge/movingpandas) 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/movingpandas/movingpandas-examples/main) 


## Features

* Easily create trajectories from diverse sources, including CSV files, GIS file formats, (Geo)DataFrames, and OGC Moving Features JSONs (MF-JSON) 
* Find locations for given time stamps and time spans
* Compute movement speed, direction, and sampling intervals
* Detect and extract stops 
* Split trajectories into individual trips
* Clean, simplify, generalize, and aggregate trajectories 
* Create static and interactive visualizations 

Here are some examples:

### Trajectory plots [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/2-analysis-examples/bird-migration.ipynb)

Create interactive trajectory plots, including multiple linked plots with ease ...

![movingpandas_animated](https://user-images.githubusercontent.com/590385/137953765-33f9ce1b-037c-4c86-82b2-0620de5ca28f.gif)


For all types of tracking data, e.g. [video-based trajectories](https://anitagraser.com/2023/05/21/analyzing-video-based-bicycle-trajectories/)

![Bicycle tracks from object tracking in videos](https://github.com/movingpandas/movingpandas/assets/590385/c4a0f682-bb94-4b15-ac03-a4d854008937)


Including plots in custom projections [![View Jupyter Notebook](https://img.shields.io/badge/view-Jupyter%20notebook-lightgrey.svg)](https://github.com/movingpandas/movingpandas-examples/blob/main/2-analysis-examples/iceberg.ipynb)

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

## What's next?

MovingPandas is under active development and there are some exciting features coming up. 
If you’d like to contribute to this project, you’re welcome to head on over to the [Github repo](https://github.com/movingpandas/movingpandas)! 


## Citation information

Please cite [0] when using MovingPandas in your research and reference the appropriate release version. All releases of MovingPandas are listed on [Zenodo](https://doi.org/10.5281/zenodo.3710950) where you will find citation information, including DOIs.  

[0] [Graser, A. (2019). MovingPandas: Efficient Structures for Movement Data in Python. GI_Forum ‒ Journal of Geographic Information Science 2019, 1-2019, 54-68. doi:10.1553/giscience2019_01_s54.](https://www.austriaca.at/rootcollection?arp=0x003aba2b)

If you are curious about who else is using MovingPandas, check out the [list of publications citing MovingPandas](https://github.com/movingpandas/movingpandas#scientific-publications-using-movingpandas).
