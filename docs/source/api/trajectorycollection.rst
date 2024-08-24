============
TrajectoryCollection
============
.. currentmodule:: movingpandas

.. autoclass:: TrajectoryCollection

   .. automethod:: __init__


Conversion 
-------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.to_line_gdf
   TrajectoryCollection.to_mf_json
   TrajectoryCollection.to_point_gdf
   TrajectoryCollection.to_traj_gdf


Enrichment
-------------------------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.add_acceleration
   TrajectoryCollection.add_angular_difference
   TrajectoryCollection.add_direction
   TrajectoryCollection.add_distance
   TrajectoryCollection.add_speed
   TrajectoryCollection.add_timedelta
   TrajectoryCollection.add_traj_id


General methods and attributes
---------------------------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.copy
   TrajectoryCollection.drop
   TrajectoryCollection.filter
   TrajectoryCollection.get_max
   TrajectoryCollection.get_min
   TrajectoryCollection.get_trajectories
   TrajectoryCollection.get_trajectory


Plotting 
------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.explore
   TrajectoryCollection.hvplot
   TrajectoryCollection.hvplot_pts
   TrajectoryCollection.plot


Spatiotemporal analysis
----------------------------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.clip
   TrajectoryCollection.get_crs
   TrajectoryCollection.get_end_locations
   TrajectoryCollection.get_intersecting
   TrajectoryCollection.get_locations_at
   TrajectoryCollection.get_segments_between
   TrajectoryCollection.get_start_locations
   TrajectoryCollection.intersection
   TrajectoryCollection.is_latlon


Spatiotemporal columns 
-------------------------------

.. autosummary::
   :toctree: api/

   TrajectoryCollection.get_column_names
   TrajectoryCollection.get_direction_col
   TrajectoryCollection.get_geom_col
   TrajectoryCollection.get_speed_col
   TrajectoryCollection.get_traj_id_col

