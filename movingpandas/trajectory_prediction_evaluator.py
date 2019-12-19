# -*- coding: utf-8 -*-

from pyproj import Proj, transform
from shapely.geometry import Point, LineString
from fiona.crs import from_epsg
from fiona.transform import transform

from .geometry_utils import measure_distance_spherical, measure_distance_euclidean


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class EvaluatedPrediction:
    def __init__(self, id, predicted_location, context, errors={}):
        self.id = id
        self.predicted_location = predicted_location
        self.errors = errors
        self.context = context
        
    def __str__(self):
        return "{} ({}): {} - Errors: {}".format(self.id, self.context, self.predicted_location, self.errors)
        
    @staticmethod
    def get_csv_header():
        return "id;predicted_location;context;distance_error;along_track_error;cross_track_error\n"
        
    def to_csv(self):
        return "{};{};{};{};{};{}\n".format(self.id, self.predicted_location, self.context, self.errors['distance'],
                                            self.errors['along_track'], self.errors['cross_track'])


class TrajectoryPredictionEvaluator:
    def __init__(self, groundtruth_sample, predicted_location, crs, input_crs=CRS_LATLON):
        self.truth = groundtruth_sample.future_pos
        self.true_traj = groundtruth_sample.future_traj
        self.prediction = predicted_location
        self.evaluation_crs = crs
        self.input_crs = input_crs
        self.linestring = self.create_linestring()
        self.projected_prediction = self.project_prediction_onto_linestring()

    def create_linestring(self):
        linestring = self.true_traj.to_linestring().coords
        return LineString([Point(self.project_point(Point(p))) for p in linestring])

    def get_errors(self):
        return {'distance': self.get_distance_error(),
                'cross_track': self.get_cross_track_error(),
                'along_track': self.get_along_track_error()}
    
    def get_distance_error(self):
        if self.input_crs == CRS_LATLON:
            return measure_distance_spherical(self.truth, self.prediction)
        else:
            return measure_distance_euclidean(self.truth, self.prediction)

    def project_point(self, pt) :
        x, y = transform(self.input_crs, self.evaluation_crs, [pt.x], [pt.y])
        return Point(x[0], y[0])
        
    def project_back(self, pt):
        lon, lat = transform(self.evaluation_crs, self.input_crs, [pt.x], [pt.y])
        return Point(lon[0], lat[0])

    def project_prediction_onto_linestring(self):
        predicted_point = self.project_point(self.prediction)
        return self.project_back(self.linestring.interpolate(self.linestring.project(predicted_point)))
        
    def get_cross_track_error(self):
        return measure_distance_spherical(self.prediction, self.projected_prediction)
        
    def get_along_track_error(self):
        truth_dist_along_line = self.linestring.project(self.truth)
        predicted_dist_along_line = self.linestring.project(self.projected_prediction)
        return abs(predicted_dist_along_line - truth_dist_along_line)

