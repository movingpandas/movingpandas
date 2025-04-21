MovingPandas.CPACalculator
===========================================
.. _cpa:

.. automodule:: movingpandas
    :noindex:

.. autoclass:: CPACalculator
   :members:

   .. automethod:: __init__
   .. automethod:: min
   .. automethod:: segments_gdf

*********
 Example
*********
This example shows how to create two trajectories and use them for a closest point of approach calculation.

.. code:: python

    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point
    from datetime import datetime, timedelta
    import movingpandas as mpd

    # Create sample data for Trajectory a
    df_a = pd.DataFrame(
        [
            {"geometry": Point(0, 0), "t": datetime(2023, 1, 1, 12, 0, 0)},
            {"geometry": Point(1, 1), "t": datetime(2023, 1, 1, 12, 3, 0)},
        ]
    ).set_index("t")
    gdf_a = gpd.GeoDataFrame(df_a, crs="EPSG:4326")
    traj_a = mpd.Trajectory(gdf_a, traj_id="A")

    # Create sample data for Trajectory b (moving closer, almost colliding)
    df_b = pd.DataFrame(
        [
            {"geometry": Point(1, 1), "t": datetime(2023, 1, 1, 12, 0, 0)},
            {"geometry": Point(0, 0.2), "t": datetime(2023, 1, 1, 12, 3, 0)},
        ]
    ).set_index("t")
    gdf_b = gpd.GeoDataFrame(df_b, crs="EPSG:4326")
    traj_b = mpd.Trajectory(gdf_b, traj_id="B")

    # Calculate CPA
    cpa_calculator = mpd.CPACalculator(traj_a, traj_b)
    cpa = cpa_calculator.min()

    # Print results
    print(f"Closest Point of Approach has a distance of {cpa.dist:.2f}m")
    print(f"Time to CPA {cpa.t_to.total_seconds():.2f}s")

    >>> Closest Point of Approach has a distance of 0.07m
    >>> Time to CPA 94.48s

*******************
 Technical Details
*******************

The CPA calculation operates on the time period where both trajectories
temporally overlap. It internally discretizes this common time interval
based on the combined timestamps of both trajectories. For each discrete
time step within the overlap, the function interpolates the position of
each object along its respective trajectory segment.

The Euclidean distance between these interpolated positions is
calculated at each time step. The function then identifies the time step
where this distance is minimized. The minimum distance, the
corresponding timestamp (which is the same for both trajectories at the
point of closest approach), and the interpolated geographical points on
each trajectory at that specific timestamp are returned.

The accuracy of the result depends on:

#. **Temporal Resolution:** Finer temporal resolution in the input
   trajectories generally leads to a more accurate CPA calculation.
#. **Interpolation Method:** MovingPandas uses linear
   interpolation for position between known points.

The method is implemented in Cartesian 3D coordinates. If you pass a trajectory
that is not projected, it will generate a warning.
>>>>>>> dba9c5d (CPA documentation)
