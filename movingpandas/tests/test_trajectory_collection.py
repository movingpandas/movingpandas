# -*- coding: utf-8 -*-

from copy import copy
from datetime import datetime as datetime, timedelta as timedelta
from math import sqrt

import pandas as pd
import pytest
from pyproj import CRS
from geopandas import GeoDataFrame
from pandas import Timestamp
from pandas.testing import assert_frame_equal
from shapely.geometry import LineString, Point, Polygon, MultiPolygon

from movingpandas.trajectory import (
    TRAJ_ID_COL_NAME,
    SPEED_COL_NAME,
    DIRECTION_COL_NAME,
    DISTANCE_COL_NAME,
    ACCELERATION_COL_NAME,
    ANGULAR_DIFFERENCE_COL_NAME,
    TIMEDELTA_COL_NAME,
)
from movingpandas.trajectory_collection import TrajectoryCollection
from . import requires_holoviews, requires_folium, has_geopandas1, requires_geopandas1

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryCollection:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0), 5, "b"],
                [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0), 2, "c"],
                [1, "A", Point(9, 9), datetime(2018, 1, 1, 14, 15, 0), 4, "d"],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0), 10, "e"],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 6, 0), 6, "f"],
                [2, "A", Point(16, 16), datetime(2018, 1, 2, 13, 10, 0), 7, "g"],
                [2, "A", Point(190, 10), datetime(2018, 1, 2, 13, 15, 0), 3, "h"],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(
            self.geo_df, traj_id_col="id", obj_id_col="obj"
        )
        self.geo_df_latlon = GeoDataFrame(df).set_crs(
            crs=CRS_LATLON, allow_override=True
        )
        self.collection_latlon = TrajectoryCollection(
            self.geo_df_latlon, "id", obj_id_col="obj"
        )

    def test_number_of_trajectories(self):
        assert len(self.collection) == 2

    def test_number_of_trajectories_nongeo_df(self):
        df = pd.DataFrame(self.geo_df)
        df["x"] = self.geo_df.geometry.x
        df["y"] = self.geo_df.geometry.y
        df = df.drop(columns="geometry")
        self.collection = TrajectoryCollection(
            df, traj_id_col="id", obj_id_col="obj", x="x", y="y"
        )
        assert len(self.collection) == 2

    def test_number_of_trajectories_min_length(self):
        collection = TrajectoryCollection(
            self.geo_df, "id", obj_id_col="obj", min_length=100
        )
        assert len(collection) == 1

    def test_number_of_trajectories_min_length_never_reached(self):
        collection = TrajectoryCollection(
            self.geo_df, "id", obj_id_col="obj", min_length=1000
        )
        assert len(collection) == 0

    def test_number_of_trajectories_min_duration(self):
        collection = TrajectoryCollection(
            self.geo_df, "id", obj_id_col="obj", min_duration=timedelta(days=1)
        )
        assert len(collection) == 1

    def test_number_of_trajectories_min_duration_from_list(self):
        collection = TrajectoryCollection(
            self.collection.trajectories, min_duration=timedelta(days=1)
        )
        assert len(collection) == 1

    def test_number_of_trajectories_min_duration_never_reached(self):
        collection = TrajectoryCollection(
            self.geo_df, "id", obj_id_col="obj", min_duration=timedelta(weeks=1)
        )
        assert len(collection) == 0

    def test_get_trajectory(self):
        assert self.collection.get_trajectory(1).id == 1
        assert self.collection.get_trajectory(1).obj_id == "A"
        assert self.collection.get_trajectory(2).id == 2
        assert self.collection.get_trajectory(3) is None

    def test_get_trajectories(self):
        assert len(self.collection.get_trajectories("A")) == 2
        assert len(self.collection.get_trajectories("A").to_point_gdf()) == 8
        assert len(self.collection.get_trajectories("B")) == 0

    def test_get_locations_at(self):
        locs = self.collection.get_locations_at(datetime(2018, 1, 1, 12, 6, 0))
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(6, 0), Point(16, 10)]
        assert locs.iloc[0].val in [5, 6]
        assert locs.iloc[1].geometry in [Point(6, 0), Point(16, 10)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry

    def test_get_locations_at_nearest(self):
        locs = self.collection.get_locations_at(datetime(2018, 1, 1, 12, 6, 1))
        assert len(locs) == 2
        assert locs.iloc[0].val in [5, 6]

    def test_get_locations_at_out_of_time_range(self):
        locs = self.collection.get_locations_at(datetime(2017, 1, 1, 12, 6, 1))
        assert len(locs) == 0

    def test_get_start_locations(self):
        locs = self.collection.get_start_locations()
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(0, 0), Point(10, 10)]
        assert locs.iloc[0].id in [1, 2]
        assert locs.iloc[0].obj == "A"
        assert locs.iloc[0].val in [9, 10]
        assert locs.iloc[0].val2 in ["a", "e"]
        assert locs.iloc[1].geometry in [Point(0, 0), Point(10, 10)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry
        assert isinstance(locs, GeoDataFrame)
        assert locs.crs == CRS_METRIC

    def test_timestamp_column_present_in_start_locations(self):
        locs = self.collection.get_start_locations()
        assert "t" in locs.columns
        assert locs["t"].tolist() == [
            Timestamp("2018-01-01 12:00:00"),
            Timestamp("2018-01-01 12:00:00"),
        ]

    def test_timestamp_column_present_in_end_locations(self):
        locs = self.collection.get_end_locations()
        assert "t" in locs.columns
        assert locs["t"].tolist() == [
            Timestamp("2018-01-01 14:15:00"),
            Timestamp("2018-01-02 13:15:00"),
        ]

    def test_get_end_locations(self):
        locs = self.collection.get_end_locations()
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(9, 9), Point(190, 10)]
        assert locs.iloc[0].id in [1, 2]
        assert locs.iloc[0].obj == "A"
        assert locs.iloc[0].val in [4, 3]
        assert locs.iloc[0].val2 in ["d", "h"]
        assert locs.iloc[1].geometry in [Point(9, 9), Point(190, 10)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry
        assert isinstance(locs, GeoDataFrame)
        assert locs.crs == CRS_METRIC

    def test_get_segments_between(self):
        collection = self.collection.get_segments_between(
            datetime(2018, 1, 1, 12, 6, 0), datetime(2018, 1, 1, 14, 10, 0)
        )
        assert len(collection) == 1
        assert collection.trajectories[0].to_linestring().wkt == "LINESTRING (6 0, 6 6)"

    def test_get_intersecting(self):
        polygon = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)])
        collection = self.collection.get_intersecting(polygon)
        assert len(collection) == 1
        assert collection.trajectories[0] == self.collection.trajectories[0]

    def test_intersection(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]],
            },
            "properties": {"id": 1, "name": "foo"},
        }
        collection = self.collection.intersection(feature)
        assert len(collection) == 1

    def test_clip(self):
        polygon = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)])
        collection = self.collection.copy()
        collection = self.collection.clip(polygon)
        assert len(collection) == 1
        assert collection.trajectories[0].to_linestring().wkt == "LINESTRING (0 0, 1 0)"

    def test_clip_with_multipolygon(self):
        polygon = MultiPolygon(
            [
                Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]),
                Polygon([(5, 1), (7, 1), (7, 3), (5, 3), (5, 1)]),
            ]
        )
        collection = self.collection.clip(polygon)
        assert len(collection) == 2
        assert collection.trajectories[0].to_linestring().wkt == "LINESTRING (0 0, 1 0)"
        assert collection.trajectories[1].to_linestring().wkt == "LINESTRING (6 1, 6 3)"

    def test_clip_with_multipolygon2(self):
        polygon = MultiPolygon(
            [
                Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]),
                Polygon([(3, -1), (3, 1), (4, 1), (4, -1), (3, -1)]),
            ]
        )
        collection = self.collection.clip(polygon)
        assert len(collection) == 2
        assert collection.trajectories[0].to_linestring().wkt == "LINESTRING (0 0, 1 0)"
        assert collection.trajectories[1].to_linestring().wkt == "LINESTRING (3 0, 4 0)"

    def test_clip_with_min_length(self):
        polygon = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)])
        collection = self.collection.copy()
        collection.min_length = 1
        collection = collection.clip(polygon)
        assert len(collection) == 1
        collection = self.collection.copy()
        collection.min_length = 2
        collection = collection.clip(polygon)
        assert len(collection) == 0

    def test_filter(self):
        assert len(self.collection.filter("obj", "A")) == 2
        assert len(self.collection.filter("obj", ["A"])) == 2
        assert len(self.collection.filter("obj", ["B"])) == 0
        assert len(self.collection.filter("obj", [1])) == 0

    def test_get_min_and_max(self):
        assert self.collection.get_min("val") == 2
        assert self.collection.get_max("val") == 10

    def test_plot_exists(self):
        from matplotlib.axes import Axes

        result = self.collection.plot()
        assert isinstance(result, Axes)

    @requires_folium
    def test_explore_exists(self):
        from folium.folium import Map

        if has_geopandas1:
            plot = self.collection.explore()
            assert isinstance(plot, Map)
        else:
            with pytest.raises(NotImplementedError):
                plot = self.collection.explore()

    @requires_holoviews
    def test_hvplot_exists(self):
        import holoviews

        result = self.collection_latlon.hvplot()
        assert isinstance(result, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot()
        assert isinstance(plot, holoviews.core.overlay.Overlay)
        assert len(plot.Path.ddims) == 2

        plot = self.collection_latlon.hvplot(color="red")
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot(c="id")
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot(c="id", colormap={1: "red", 2: "blue"})
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot_pts()
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot_pts(c="id")
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot_pts(c="speed")
        assert isinstance(plot, holoviews.core.overlay.Overlay)

        plot = self.collection_latlon.hvplot_pts(c="id", colormap={1: "red", 2: "blue"})
        assert isinstance(plot, holoviews.core.overlay.Overlay)

    def test_plot_existing_column(self):
        from matplotlib.axes import Axes

        result = self.collection.plot(column="val")
        assert isinstance(result, Axes)

    def test_plot_speed(self):
        from matplotlib.axes import Axes

        result = self.collection.plot(column="speed")
        assert isinstance(result, Axes)

    def test_plot_speed_not_altering_collection(self):
        self.collection.plot(column="speed")
        assert all(
            [
                "speed" not in traj.df.columns.values
                for traj in self.collection.trajectories
            ]
        )

    @requires_geopandas1
    @requires_folium
    def test_explore_speed_not_altering_collection(self):
        self.collection.explore(column="speed")
        assert all(
            [
                "speed" not in traj.df.columns.values
                for traj in self.collection.trajectories
            ]
        )

    @requires_geopandas1
    @requires_folium
    def test_explore_speed(self):
        from folium.folium import Map

        result = self.collection.explore(column="speed")
        assert isinstance(result, Map)

    def test_traj_with_less_than_two_points(self):
        df = pd.DataFrame(
            [[1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"]],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        tc = TrajectoryCollection(geo_df, "id", obj_id_col="obj")
        assert len(tc) == 0

    def test_traj_with_two_points_at_the_same_time(self):
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        tc = TrajectoryCollection(geo_df, "id", obj_id_col="obj")
        assert len(tc) == 0

    def test_iteration(self):
        assert sum([1 for _ in self.collection]) == len(self.collection)

    def test_iteration_error(self):
        def filter_trajectory(trajectory):
            trajectory.df = trajectory.df[trajectory.df["val"] >= 7]
            return trajectory

        trajs = [filter_trajectory(traj) for traj in self.collection]

        lengths = (1, 2)
        for traj, length in zip(trajs, lengths):
            assert len(traj.df) == length

        collection = copy(self.collection)
        collection.trajectories = trajs
        with pytest.raises(ValueError):
            for _ in collection:
                pass

    def test_add_traj_id(self):
        self.collection.add_traj_id()
        result1 = self.collection.trajectories[0].df[TRAJ_ID_COL_NAME].tolist()
        assert result1 == [1, 1, 1, 1]
        result2 = self.collection.trajectories[1].df[TRAJ_ID_COL_NAME].tolist()
        assert result2 == [2, 2, 2, 2]

    def test_add_traj_id_overwrite_raises_error(self):
        gdf = self.geo_df.copy()
        gdf[TRAJ_ID_COL_NAME] = "a"
        collection = TrajectoryCollection(gdf, "id", obj_id_col="obj")
        with pytest.raises(RuntimeError):
            collection.add_traj_id()

    def test_add_speed(self):
        self.collection.add_speed()
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[SPEED_COL_NAME].tolist()
        assert result0[0] == pytest.approx(0.01667, 0.001)
        result1 = self.collection.trajectories[1].df[SPEED_COL_NAME].tolist()
        assert result1[0] == pytest.approx(0.01667, 0.001)
        assert len(result0) == 4

    def test_add_speed_multiprocessing(self):
        self.collection.trajectories += self.collection.trajectories
        expected = self.collection.copy()
        expected.add_speed()
        self.collection.add_speed(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[SPEED_COL_NAME].tolist()
        assert result0 == expected.trajectories[0].df[SPEED_COL_NAME].tolist()
        result1 = self.collection.trajectories[-1].df[SPEED_COL_NAME].tolist()
        assert result1 == expected.trajectories[-1].df[SPEED_COL_NAME].tolist()
        assert len(expected.trajectories) == len(self.collection.trajectories)
        assert len(expected.trajectories) == 4

    def test_add_acceleration(self):
        self.collection.add_acceleration()
        result1 = self.collection.trajectories[0].df[ACCELERATION_COL_NAME].tolist()
        assert len(result1) == 4

    def test_add_acceleration_multiprocessing(self):
        expected = self.collection.copy()
        expected.add_acceleration()
        print(expected.to_point_gdf())
        self.collection.add_acceleration(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[ACCELERATION_COL_NAME].tolist()
        assert result0 == expected.trajectories[0].df[ACCELERATION_COL_NAME].tolist()
        result1 = self.collection.trajectories[1].df[ACCELERATION_COL_NAME].tolist()
        assert result1 == expected.trajectories[1].df[ACCELERATION_COL_NAME].tolist()

    def test_add_direction(self):
        self.collection.add_direction()
        result = self.collection.trajectories[0].df[DIRECTION_COL_NAME].tolist()
        assert len(result) == 4

    def test_add_direction_multiprocessing(self):
        expected = self.collection.copy()
        expected.add_direction()
        print(expected.to_point_gdf())
        self.collection.add_direction(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[DIRECTION_COL_NAME].tolist()
        assert result0 == expected.trajectories[0].df[DIRECTION_COL_NAME].tolist()
        result1 = self.collection.trajectories[1].df[DIRECTION_COL_NAME].tolist()
        assert result1 == expected.trajectories[1].df[DIRECTION_COL_NAME].tolist()

    def test_add_distance(self):
        self.collection.add_distance()
        result0 = self.collection.trajectories[0].df[DISTANCE_COL_NAME].tolist()
        assert len(result0) == 4

    def test_add_distance_multiprocessing(self):
        expected = self.collection.copy()
        expected.add_distance()
        print(expected.to_point_gdf())
        self.collection.add_distance(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[DISTANCE_COL_NAME].tolist()
        assert result0 == expected.trajectories[0].df[DISTANCE_COL_NAME].tolist()
        result1 = self.collection.trajectories[1].df[DISTANCE_COL_NAME].tolist()
        assert result1 == expected.trajectories[1].df[DISTANCE_COL_NAME].tolist()

    def test_add_angular_difference(self):
        self.collection.add_angular_difference()
        result1 = (
            self.collection.trajectories[0].df[ANGULAR_DIFFERENCE_COL_NAME].tolist()
        )
        assert len(result1) == 4

    def test_add_angular_difference_multiprocessing(self):
        expected = self.collection.copy()
        expected.add_angular_difference()
        print(expected.to_point_gdf())
        self.collection.add_angular_difference(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = (
            self.collection.trajectories[0].df[ANGULAR_DIFFERENCE_COL_NAME].tolist()
        )
        assert (
            result0 == expected.trajectories[0].df[ANGULAR_DIFFERENCE_COL_NAME].tolist()
        )
        result1 = (
            self.collection.trajectories[1].df[ANGULAR_DIFFERENCE_COL_NAME].tolist()
        )
        assert (
            result1 == expected.trajectories[1].df[ANGULAR_DIFFERENCE_COL_NAME].tolist()
        )

    def test_add_timedelta(self):
        self.collection.add_timedelta()
        result1 = self.collection.trajectories[0].df[TIMEDELTA_COL_NAME].tolist()
        assert len(result1) == 4

    def test_add_timedelta_multiprocessing(self):
        expected = self.collection.copy()
        expected.add_timedelta()
        print(expected.to_point_gdf())
        self.collection.add_timedelta(n_processes=2)
        print(self.collection.to_point_gdf())
        result0 = self.collection.trajectories[0].df[TIMEDELTA_COL_NAME].tolist()
        assert result0 == expected.trajectories[0].df[TIMEDELTA_COL_NAME].tolist()
        result1 = self.collection.trajectories[1].df[TIMEDELTA_COL_NAME].tolist()
        assert result1 == expected.trajectories[1].df[TIMEDELTA_COL_NAME].tolist()

    def test_to_point_gdf(self, tmp_path):
        point_gdf = self.collection.to_point_gdf()
        gpkg_path = tmp_path / "temp.gpkg"
        point_gdf.to_file(gpkg_path, layer="points", driver="GPKG")
        assert gpkg_path.exists()
        assert_frame_equal(point_gdf, self.geo_df)

    def test_to_line_gdf(self, tmp_path):
        temp_df = self.geo_df.drop(columns=["obj", "val", "val2"])
        tc = TrajectoryCollection(temp_df, "id")
        line_gdf = tc.to_line_gdf()
        gpkg_path = tmp_path / "temp.gpkg"
        line_gdf.to_file(gpkg_path, layer="lines", driver="GPKG")
        assert gpkg_path.exists()
        t1 = [
            datetime(2018, 1, 1, 12, 0),
            datetime(2018, 1, 1, 12, 6),
            datetime(2018, 1, 1, 14, 10),
            datetime(2018, 1, 1, 14, 15),
        ]
        t2 = [
            datetime(2018, 1, 1, 12, 0, 0),
            datetime(2018, 1, 1, 12, 6, 0),
            datetime(2018, 1, 2, 13, 10, 0),
            datetime(2018, 1, 2, 13, 15, 0),
        ]
        df2 = pd.DataFrame(
            [
                [1, t1[1], t1[0], LineString([(0, 0), (6, 0)])],
                [1, t1[2], t1[1], LineString([(6, 0), (6, 6)])],
                [1, t1[3], t1[2], LineString([(6, 6), (9, 9)])],
                [2, t2[1], t2[0], LineString([(10, 10), (16, 10)])],
                [2, t2[2], t2[1], LineString([(16, 10), (16, 16)])],
                [2, t2[3], t2[2], LineString([(16, 16), (190, 10)])],
            ],
            columns=["id", "t", "prev_t", "geometry"],
        )
        expected_line_gdf = GeoDataFrame(df2, crs=CRS_METRIC)
        assert_frame_equal(line_gdf, expected_line_gdf)

    def test_to_traj_gdf(self, tmp_path):
        temp_df = self.geo_df.drop(columns=["obj", "val", "val2"])
        tc = TrajectoryCollection(temp_df, "id")
        traj_gdf = tc.to_traj_gdf()
        gpkg_path = tmp_path / "temp.gpkg"
        traj_gdf.to_file(gpkg_path, layer="trajs", driver="GPKG")
        assert gpkg_path.exists()
        rows = [
            {
                "id": 1,
                "start_t": datetime(2018, 1, 1, 12, 0, 0),
                "end_t": datetime(2018, 1, 1, 14, 15, 0),
                "geometry": LineString([(0, 0), (6, 0), (6, 6), (9, 9)]),
                "length": 12 + sqrt(18),
                "direction": 45.0,
            },
            {
                "id": 2,
                "start_t": datetime(2018, 1, 1, 12, 0, 0),
                "end_t": datetime(2018, 1, 2, 13, 15, 0),
                "geometry": LineString([(10, 10), (16, 10), (16, 16), (190, 10)]),
                "length": 12 + sqrt(174 * 174 + 36),
                "direction": 90.0,
            },
        ]
        df2 = pd.DataFrame(rows)
        expected_line_gdf = GeoDataFrame(df2, crs=CRS_METRIC)

        assert_frame_equal(traj_gdf, expected_line_gdf)

    def test_to_traj_gdf_aggregate(self):
        temp_df = self.geo_df.drop(columns=["val2"])
        tc = TrajectoryCollection(temp_df, "id")
        traj_gdf = tc.to_traj_gdf(
            agg={"obj": "mode", "val": ["min", "q5", "q75", "max"]}
        )
        print(traj_gdf)
        rows = [
            {
                "id": 1,
                "start_t": datetime(2018, 1, 1, 12, 0, 0),
                "end_t": datetime(2018, 1, 1, 14, 15, 0),
                "geometry": LineString([(0, 0), (6, 0), (6, 6), (9, 9)]),
                "length": 12 + sqrt(18),
                "direction": 45.0,
                "obj_mode": "A",
                "val_min": 2,
                "val_q5": 2.3,
                "val_q75": 6.0,
                "val_max": 9,
            },
            {
                "id": 2,
                "start_t": datetime(2018, 1, 1, 12, 0, 0),
                "end_t": datetime(2018, 1, 2, 13, 15, 0),
                "geometry": LineString([(10, 10), (16, 10), (16, 16), (190, 10)]),
                "length": 12 + sqrt(174 * 174 + 36),
                "direction": 90.0,
                "obj_mode": "A",
                "val_min": 3,
                "val_q5": 3.45,
                "val_q75": 7.75,
                "val_max": 10,
            },
        ]
        df2 = pd.DataFrame(rows)
        expected_line_gdf = GeoDataFrame(df2, crs=CRS_METRIC)

        assert_frame_equal(traj_gdf, expected_line_gdf)

    def test_to_mf_json(self):
        json = self.collection.to_mf_json(datetime_to_str=False)
        assert (
            str(json)
            == """{'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'id': 1, 'obj': 'A', 'val': 9, 'val2': 'a'}, 'temporalGeometry': {'type': 'MovingPoint', 'coordinates': [(0.0, 0.0), (6.0, 0.0), (6.0, 6.0), (9.0, 9.0)], 'datetimes': [Timestamp('2018-01-01 12:00:00'), Timestamp('2018-01-01 12:06:00'), Timestamp('2018-01-01 14:10:00'), Timestamp('2018-01-01 14:15:00')]}}, {'type': 'Feature', 'properties': {'id': 2, 'obj': 'A', 'val': 10, 'val2': 'e'}, 'temporalGeometry': {'type': 'MovingPoint', 'coordinates': [(10.0, 10.0), (16.0, 10.0), (16.0, 16.0), (190.0, 10.0)], 'datetimes': [Timestamp('2018-01-01 12:00:00'), Timestamp('2018-01-01 12:06:00'), Timestamp('2018-01-02 13:10:00'), Timestamp('2018-01-02 13:15:00')]}}]}"""  # noqa F401
        )

    def test_deprecation_warning_when_using_n_threads(self):
        with pytest.deprecated_call():
            self.collection.add_speed(n_threads=2)
