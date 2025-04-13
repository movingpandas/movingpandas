import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely

import pytest

import movingpandas as mpd
from movingpandas.cpa import CPACalculator

# create local coordinate system
# or use a projected system?
crs_wkt = """
ENGCRS["Custom 3D Cartesian Engineering CRS",
    EDATUM["Local Engineering Datum"],
    CS[Cartesian,3],
    AXIS["east (x)", east],
    AXIS["north (y)", north],
    AXIS["up (z)", up],
    LENGTHUNIT["metre",1.0]
]
"""
crs = pyproj.CRS.from_wkt(crs_wkt)


@pytest.fixture
def traj_a():
    """trajectory a of postgis docs"""
    # https://postgis.net/docs/ST_DistanceCPA.html
    point_0 = shapely.Point(0, 0, 0)
    point_1 = shapely.Point(10, 0, 5)
    points = [point_0, point_1]
    date_0 = datetime.datetime(2015, 5, 26, 10, 0)
    date_1 = datetime.datetime(2015, 5, 26, 11, 0)
    t = [date_0, date_1]
    gdf = gpd.GeoDataFrame(data=dict(t=t), geometry=points, crs=crs)
    traj = mpd.Trajectory(gdf, traj_id="traj_a", t="t", crs=crs)
    return traj


@pytest.fixture
def traj_b():
    """trajectory b of postgis docs"""
    # https://postgis.net/docs/ST_DistanceCPA.html
    point_0 = shapely.Point(0, 2, 10)
    point_1 = shapely.Point(12, 1, 2)
    points = [point_0, point_1]
    date_0 = datetime.datetime(2015, 5, 26, 10, 0)
    date_1 = datetime.datetime(2015, 5, 26, 11, 0)
    t = [date_0, date_1]
    gdf = gpd.GeoDataFrame(data=dict(t=t), geometry=points, crs=crs)
    traj = mpd.Trajectory(gdf, traj_id="traj_b", t="t", crs=crs)
    return traj


def create_traj(p0: tuple, p1: tuple, t0: float, t1: float):
    """Create a trajectory based on two points and two floating point times"""
    point_0 = shapely.Point(*p0)
    point_1 = shapely.Point(*p1)
    points = [point_0, point_1]
    # make sure we get non-local date naive dates
    date_0 = datetime.datetime.fromtimestamp(t0, tz=datetime.UTC)
    date_0 = date_0.replace(tzinfo=None)

    date_1 = datetime.datetime.fromtimestamp(t1, tz=datetime.UTC)
    date_1 = date_1.replace(tzinfo=None)
    t = [date_0, date_1]

    gdf = gpd.GeoDataFrame(data=dict(t=t), geometry=points, crs=crs)
    traj = mpd.Trajectory(gdf, traj_id="traj", t="t", crs=crs)
    return traj


def test_invalid_trajectory(traj_a, traj_b):
    with pytest.raises(TypeError):
        # should not work if you pass a data frame
        CPACalculator(traj_a.df, traj_b)


def test_postgis_example(traj_a, traj_b):
    cpa = CPACalculator(traj_a, traj_b)
    cpa.min()

    # TODO: postgis finds, why do we have 1.965....
    # Expected: 1.96036833151395
    #
    # Postgis docs are not consistent whether 3d is used:
    # - Returns the distance (in 2D) between two trajectories at their closest point of approach.
    # - This function supports 3d and will not drop the z-index.
    # 2d gives: 1.7888543819

    np.testing.assert_almost_equal(cpa.min().dist, 1.965214737762069)


def test_non_overlapping_time():
    traj_a = create_traj((0, 0), (0, 0), 0, 1)
    traj_b = create_traj((0, 0), (0, 0), 2, 5)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # we should have NaT and NaN  (postgis returns time of -2)
    assert pd.isna(
        result.t_at
    ), f"cpa.t should be NaT if times do not overlap, got {result.t_at}"
    assert pd.isna(
        result.dist
    ), f"cpa.t should be NaT if times do not overlap, got {result.dist}"


def test_two_stationary_touching_time():
    """Two stationary tracks, timestamps touch."""

    traj_a = create_traj((0, 0), (0, 0), 0, 1)
    traj_b = create_traj((0, 0), (0, 0), 1, 5)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 1.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);
    assert result.t_at.timestamp() == 1, "t should equal 1"
    assert result.dist == 0, "t should equal 0"
    assert result.status == "touching", "status should should be touching"


def test_one_stationary_one_moving():
    """One of the tracks is stationary, the other passes at 10 meters from point"""
    traj_a = create_traj((0, 0), (0, 0), 1, 5)
    traj_b = create_traj((-10, 10), (10, 10), 1, 5)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 3.0);
    # ASSERT_DOUBLE_EQUAL(dist, 10.0);
    #
    assert result.t_at.timestamp() == 3, "time of cpa should be 3"
    assert result.dist == 10, "distance should be 10"
    assert result.status == "approaching", "distance should be 10"


def test_equal_trajectories():
    """Equal tracks, 2d"""
    traj_a = create_traj((0, 0), (10, 0), 10, 20)
    traj_b = create_traj((0, 0), (10, 0), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 10.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);
    assert result.t_at.timestamp() == 10, "t should equal 10"
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "parallel", "status should be parallel"


def test_inverse_trajectories():
    """Reversed tracks, 2d"""
    traj_a = create_traj((0, 0), (10, 0), 10, 20)
    traj_b = create_traj((10, 0), (0, 0), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 15.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);
    assert result.t_at.timestamp() == 15, "t should equal 15"
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "approaching", "status should be approaching"


def test_parallel_trajectories():
    """Parallel tracks, same speed, 2d"""

    traj_a = create_traj((2, 0), (12, 0), 10, 20)
    traj_b = create_traj((13, 0), (23, 0), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 10.0);
    # ASSERT_DOUBLE_EQUAL(dist, 11.0);
    assert result.t_at.timestamp() == 10, "t should equal 10"
    assert result.dist == 11, "distance should equal 11"
    assert result.status == "parallel", "status should be parallel"


def test_parallel_b_faster():
    """Parallel tracks, different speed (g2 gets closer as time passes), 2d"""

    # 0.6m/s
    traj_a = create_traj((4, 0), (10, 0), 10, 20)
    # 0.7m/s
    traj_b = create_traj((2, 0), (9, 0), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()
    # ASSERT_DOUBLE_EQUAL(m, 20.0);
    # ASSERT_DOUBLE_EQUAL(dist, 1.0);

    assert result.t_at.timestamp() == 20, "t should equal 20"
    assert result.dist == 1, "distance should equal 1"
    assert result.status == "converging", "status should be converging"


def test_parallel_a_faster():
    """Parallel tracks, different speed (g2 left behind as time passes), 2d"""

    # 0.6m/s
    traj_a = create_traj((4, 0), (10, 0), 10, 20)
    # 0.4m/s
    traj_b = create_traj((2, 0), (6, 0), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()
    # ASSERT_DOUBLE_EQUAL(m, 10.0);
    # ASSERT_DOUBLE_EQUAL(dist, 2.0);
    assert result.t_at.timestamp() == 10, "t should equal 10"
    assert result.dist == 2, "distance should equal 2"
    assert result.status == "diverging", "status should be diverging"


def test_collision():
    """Tracks, colliding, 2d"""
    traj_a = create_traj((0, 0), (10, 0), 0, 10)
    traj_b = create_traj((5, -8), (5, 8), 0, 10)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 5.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);
    assert result.t_at.timestamp() == 5, "t should equal 5"
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "approaching", "status should be approaching"


def test_crossing():
    """Tracks crossing, NOT colliding, 2d"""
    traj_a = create_traj((0, 0), (10, 0), 0, 10)
    traj_b = create_traj((8, -5), (8, 5), 0, 10)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 6.5);
    # ASSERT_DOUBLE_EQUAL(rint(dist*100), 212.0);

    np.testing.assert_almost_equal(
        result.t_at.timestamp(), 6.5, err_msg="t should equal 6.5"
    )
    np.testing.assert_almost_equal(
        result.dist, 2.121320, decimal=5, err_msg="distance should equal 212"
    )
    assert result.status == "approaching", "status should be approaching"


def test_touch_start():
    """Same origin, different direction, 2d"""

    traj_a = create_traj((0, 0), (10, 0), 1, 10)
    traj_b = create_traj((0, 0), (-100, 0), 1, 10)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 1.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);

    assert result.t_at.timestamp() == 1, "t should equal 1"
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "approaching", "status should be approaching"


def test_touch_end():
    """Same ending, different direction, 2d"""

    traj_a = create_traj((10, 0), (0, 0), 1, 10)
    traj_b = create_traj((0, -100), (0, 0), 1, 10)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 10.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);
    assert result.t_at.timestamp() == 10, "t should equal 10"
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "approaching", "status should be approaching"


def test_converging_3d():
    """Converging tracks, 3d"""
    traj_a = create_traj((0, 0, 0), (10, 0, 0), 10, 20)
    traj_b = create_traj((0, 0, 8), (10, 0, 5), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()
    # ASSERT_DOUBLE_EQUAL(m, 20.0);
    # ASSERT_DOUBLE_EQUAL(dist, 5.0);
    #
    assert result.t_at.timestamp() == 20, "t should equal 20"
    assert result.dist == 5, "distance should equal 5"
    assert result.status == "approaching", "status should be approaching"


def test_stop_and_pass():
    """
    traj_a stops at t=1 until t=4 to let traj_b pass by, then continues
    traj_b passes at 1 meter from traj_a t=3
    """

    points_a = [(0, 0), (0, 1), (0, 1), (0, 10)]
    t_a = [0, 1, 4, 13]
    t_a = [
        datetime.datetime.fromtimestamp(t, tz=datetime.UTC).replace(tzinfo=None)
        for t in t_a
    ]
    points_b = [(-10, 2), (0, 2), (12, 2)]
    t_b = [0, 3, 13]
    t_b = [
        datetime.datetime.fromtimestamp(t, tz=datetime.UTC).replace(tzinfo=None)
        for t in t_b
    ]

    geometry_a = [shapely.Point(*point) for point in points_a]
    df_a = pd.DataFrame(data=dict(t=t_a))
    gdf_a = gpd.GeoDataFrame(df_a, geometry=geometry_a, crs=crs)
    traj_a = mpd.Trajectory(gdf_a, traj_id="traj_a", t="t", crs=crs)

    geometry_b = [shapely.Point(*point) for point in points_b]
    df_b = pd.DataFrame(data=dict(t=t_b))
    gdf_b = gpd.GeoDataFrame(df_b, geometry=geometry_b, crs=crs)
    traj_b = mpd.Trajectory(gdf_b, traj_id="traj_b", t="t", crs=crs)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 3.0);
    # ASSERT_DOUBLE_EQUAL(dist, 1.0);
    assert result.t_at.timestamp() == 3, "t should equal 3"
    assert result.dist == 1, "distance should equal 1"
    assert result.status == "approaching", "status should be approaching"


def test_converging_3d():
    """Converging tracks, 3d"""
    traj_a = create_traj((0, 0, 0), (10, 0, 0), 10, 20)
    traj_b = create_traj((0, 0, 8), (10, 0, 5), 10, 20)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()
    # ASSERT_DOUBLE_EQUAL(m, 20.0);
    # ASSERT_DOUBLE_EQUAL(dist, 5.0);
    assert result.t_at.timestamp() == 20, "t should equal 20"
    assert result.dist == 5, "distance should equal 5"
    assert result.status == "converging", "status should be converging"


def test_miliseconds():
    """Test related to subsecond timestamps https://trac.osgeo.org/postgis/ticket/3136"""

    points_a = [(0, 0), (2, 0)]
    t_a = [1432291464, 1432291536]
    # convert to datetime
    t_a = [
        datetime.datetime.fromtimestamp(t, tz=datetime.UTC).replace(tzinfo=None)
        for t in t_a
    ]
    geometry_a = [shapely.Point(*point) for point in points_a]
    df_a = pd.DataFrame(data=dict(t=t_a))
    gdf_a = gpd.GeoDataFrame(df_a, geometry=geometry_a, crs=crs)
    traj_a = mpd.Trajectory(gdf_a, traj_id="traj_a", t="t", crs=crs)

    points_b = [(0, 0), (1, 0), (2, 0)]
    t_b = [1432291464, 1432291466.25, 1432291500]
    # convert to datetime
    t_b = [
        datetime.datetime.fromtimestamp(t, tz=datetime.UTC).replace(tzinfo=None)
        for t in t_b
    ]
    geometry_b = [shapely.Point(*point) for point in points_b]
    df_b = pd.DataFrame(data=dict(t=t_b))
    gdf_b = gpd.GeoDataFrame(df_b, geometry=geometry_b, crs=crs)
    traj_b = mpd.Trajectory(gdf_b, traj_id="traj_b", t="t", crs=crs)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()
    # ASSERT_DOUBLE_EQUAL(m, 1432291464.0);
    # ASSERT_DOUBLE_EQUAL(dist, 0.0);

    np.testing.assert_almost_equal(
        result.t_at.timestamp(), 1432291464.0, err_msg="t should equal 1432291464.0"
    )
    assert result.dist == 0, "distance should equal 0"
    assert result.status == "approaching", "status should be approaching"


def test_single_point():
    """Tracks share a single point in time"""

    traj_a = create_traj((0, 0), (1, 0), 0, 2)
    traj_b = create_traj((0, 0), (1, 0), 2, 3)

    cpa = CPACalculator(traj_a, traj_b)
    result = cpa.min()

    # ASSERT_DOUBLE_EQUAL(m, 2.0);
    # ASSERT_DOUBLE_EQUAL(dist, 1.0);
    #
    assert result.t_at.timestamp() == 2, "t should equal 2"
    assert result.dist == 1, "distance should equal 1"
    assert result.status == "touching", "status should be touching"
