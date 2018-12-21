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

from geometry_utils import measure_distance_spherical


class EvaluatedPrediction():
    def __init__(self, predicted_location, context, errors={}):
        self.predicted_location = predicted_location
        self.errors = errors
        self.context = context
        
    def __str__(self):
        return "{}: {} - Errors: {}".format(self.context, self.predicted_location, self.errors)
        
    @staticmethod
    def get_csv_header():
        return "predicted_location;context;distance_error;along_track_error;cross_track_error\n"        
        
    def to_csv(self):
        return "{};{};{};{};{}\n".format(self.predicted_location, self.context, self.errors['distance'], self.errors['along_track'], self.errors['cross_track'])


class TrajectoryPredictionEvaluator():
    def __init__(self, groundtruth_sample, predicted_location):
        self.truth = groundtruth_sample.future_pos
        self.true_traj = groundtruth_sample.future_traj
        self.prediction = predicted_location
        self.crs = Proj(init='epsg:25832')
        self.projected_prediction = self.project_prediction_on_trajectory()
        
    def get_errors(self):
        return {'distance': self.get_distance_error(),
                'cross_track': self.get_cross_track_error(),
                'along_track': self.get_along_track_error()}
    
    def get_distance_error(self):
        return measure_distance_spherical(self.truth, self.prediction)

    def project_point(self, pt) :
        x, y = transform(Proj(init='epsg:4326'), self.crs, pt.x, pt.y)
        return Point(x, y)
        
    def project_back(self, pt):
        lon, lat = transform(self.crs, Proj(init='epsg:4326'), pt.x, pt.y)
        return Point(lon, lat)   
        
    def project_prediction_on_trajectory(self):
        traj = self.true_traj.to_linestring().coords
        traj = LineString([Point(self.project_point(Point(p))) for p in traj])
        predicted_point = self.project_point(self.prediction)
        return self.project_back(traj.interpolate(traj.project(predicted_point)))
        
    def get_cross_track_error(self):
        return measure_distance_spherical(self.prediction, self.projected_prediction)
        
    def get_along_track_error(self):
        return measure_distance_spherical(self.truth, self.projected_prediction)
        
        
        