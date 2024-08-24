============
Trajectory
============
.. currentmodule:: movingpandas

.. autoclass:: Trajectory

   .. automethod:: __init__


Conversion 
-------------

.. autosummary::
   :toctree: api/

   Trajectory.to_line_gdf
   Trajectory.to_linestring
   Trajectory.to_linestringm_wkt
   Trajectory.to_mf_json
   Trajectory.to_point_gdf
   Trajectory.to_traj_gdf


Enrichment
-------------------------------

.. autosummary::
   :toctree: api/

   Trajectory.add_acceleration
   Trajectory.add_angular_difference
   Trajectory.add_direction
   Trajectory.add_distance
   Trajectory.add_speed
   Trajectory.add_timedelta
   Trajectory.add_traj_id


General methods and attributes
---------------------------------

.. autosummary::
   :toctree: api/

   Trajectory.copy
   Trajectory.drop
   Trajectory.get_max
   Trajectory.get_min
   Trajectory.is_valid
   Trajectory.size


Plotting 
------------

.. autosummary::
   :toctree: api/

   Trajectory.explore
   Trajectory.hvplot
   Trajectory.hvplot_pts
   Trajectory.plot


.. image:: https://github.com/movingpandas/movingpandas/assets/590385/c4a0f682-bb94-4b15-ac03-a4d854008937
   :alt: hvplot examle
   :width: 500px
   :align: center


Spatiotemporal analysis
----------------------------------

.. autosummary::
   :toctree: api/

   Trajectory.clip
   Trajectory.distance
   Trajectory.get_bbox
   Trajectory.get_crs
   Trajectory.get_direction
   Trajectory.get_duration
   Trajectory.get_end_location
   Trajectory.get_end_time
   Trajectory.get_length
   Trajectory.get_linestring_between
   Trajectory.get_mcp
   Trajectory.get_position_at
   Trajectory.get_row_at
   Trajectory.get_sampling_interval
   Trajectory.get_segment_between
   Trajectory.get_start_location
   Trajectory.get_start_time
   Trajectory.hausdorff_distance
   Trajectory.interpolate_position_at
   Trajectory.intersection
   Trajectory.intersects
   Trajectory.is_latlon
   Trajectory.to_crs


Spatiotemporal columns 
-------------------------------

.. autosummary::
   :toctree: api/

   Trajectory.get_angular_difference_col
   Trajectory.get_column_names
   Trajectory.get_direction_col
   Trajectory.get_distance_col
   Trajectory.get_geom_col
   Trajectory.get_speed_col
   Trajectory.get_timedelta_col
   Trajectory.get_traj_id_col
