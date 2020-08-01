<p align="center">
  <img src="pics/movingpandas.png" alt="MovingPandas logo">
</p>

MovingPandas implements Trajectory data structures and corresponding methods for handling movement data
based on [GeoPandas](https://geopandas.org).

The official documentation is hosted on [ReadTheDocs](https://movingpandas.readthedocs.io).

For an example use case, check out our [movement data exploration tutorial](./exploration.html).


## Features

* Convert GeoPandas GeoDataFrames of time-stamped points into MovingPandas Trajectories and TrajectoryCollections
* Add trajectory properties, such as movement speed and direction
* Split continuous observations into individual trips
* Generalize Trajectories 
* Aggregate TrajectoryCollections into flow maps
* Create static and interactive visualizations for data exploration

 ![Interactive trajectory visualization using hvplot](pics/movingpandas_hvplot2.gif)


## Tutorials

All MovingPandas tutorials are available on MyBinder - no installation required: 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/anitagraser/movingpandas/binder-tag?filepath=tutorials/0_getting_started.ipynb)

![AIS trajectory example](https://user-images.githubusercontent.com/590385/73123652-4eeab080-3f92-11ea-9fb3-15afafcdb33f.PNG)
![Bird migration trajectory example](https://user-images.githubusercontent.com/590385/73123664-5ad67280-3f92-11ea-8b42-02a0135f0f5c.PNG)


## Citation information

Please cite Graser (2019) when using MovingPandas in your research.

[Graser, A. (2019). MovingPandas: Efficient Structures for Movement Data in Python. GI_Forum ‒ Journal of Geographic Information Science 2019, 1-2019, 54-68. doi:10.1553/giscience2019_01_s54.](https://www.austriaca.at/rootcollection?arp=0x003aba2b)
