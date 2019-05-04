# -*- coding: utf-8 -*-

"""
***************************************************************************
    trajectory_prediction_evaluator.py
    ---------------------
    Date                 : December 2018
    Copyright            : (C) 2018 by Anita Graser
    Email                : anitagraser@gmx.at
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from pyproj import Proj, transform
from shapely.geometry import Point, LineString

from geometry_utils import measure_distance_spherical, measure_distance_euclidean


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
    def __init__(self, groundtruth_sample, predicted_location, crs, input_crs='epsg:4326'):
        self.truth = groundtruth_sample.future_pos
        self.true_traj = groundtruth_sample.future_traj
        self.prediction = predicted_location
        self.evaluation_crs = Proj(init=crs)
        self.input_crs = Proj(init=input_crs)
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
        if self.input_crs.is_latlong():
            return measure_distance_spherical(self.truth, self.prediction)
        else:
            return measure_distance_euclidean(self.truth, self.prediction)

    def project_point(self, pt) :
        x, y = transform(self.input_crs, self.evaluation_crs, pt.x, pt.y)
        return Point(x, y)
        
    def project_back(self, pt):
        lon, lat = transform(self.evaluation_crs, self.input_crs, pt.x, pt.y)
        return Point(lon, lat)   

    def project_prediction_onto_linestring(self):
        predicted_point = self.project_point(self.prediction)
        return self.project_back(self.linestring.interpolate(self.linestring.project(predicted_point)))
        
    def get_cross_track_error(self):
        return measure_distance_spherical(self.prediction, self.projected_prediction)
        
    def get_along_track_error(self):
        truth_dist_along_line = self.linestring.project(self.truth)
        predicted_dist_along_line = self.linestring.project(self.projected_prediction)
        return abs(predicted_dist_along_line - truth_dist_along_line)

