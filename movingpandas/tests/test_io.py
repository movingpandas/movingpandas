import os
from fiona.crs import from_epsg
from movingpandas.io import read_gpx_to_trajectory
from movingpandas.trajectory import Trajectory

CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)

TEST_DATA = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 
    'data')

class TestGPXLoad:
    def setup_method(self):
        test_run_file = os.path.join(TEST_DATA, 'run.gpx')

        self.run_trajectory = read_gpx_to_trajectory(test_run_file)
        self.run_trajectory_metric = read_gpx_to_trajectory(test_run_file, CRS_METRIC)
        self.run_trajectory_latlon = read_gpx_to_trajectory(test_run_file, CRS_LATLON)

    def test_read_success(self):
        assert isinstance(self.run_trajectory, Trajectory)
        assert isinstance(self.run_trajectory_metric, Trajectory)
        assert isinstance(self.run_trajectory_latlon, Trajectory)

    def test_default_crs(self):
        assert self.run_trajectory.crs == '+init=epsg:4326 +type=crs'

    def test_metric_conversion(self):
        assert self.run_trajectory_metric.crs == CRS_METRIC

    def test_latlon_conversion(self):
        assert self.run_trajectory_latlon.crs == CRS_LATLON

    def test_read_all_records(self):
        assert self.run_trajectory.df.shape[0] == 205
    
