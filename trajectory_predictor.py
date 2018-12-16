# -*- coding: utf-8 -*-

"""
***************************************************************************
    trajectory_predictor.py
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

import pandas as pd
from math import sin, cos, atan2, radians, degrees, asin, sqrt
from datetime import timedelta
from shapely.geometry import Point

from geometry_utils import calculate_initial_compass_bearing, measure_distance_spherical, R_EARTH


class TrajectoryPredictor():
    def __init__(self, traj):
        self.traj = traj
        
    def calculate_current_cog_and_sog(self):
        point1 = self.traj.get_start_location()
        point2 = self.traj.get_end_location()
        t1 = self.traj.get_start_time()
        t2 = self.traj.get_end_time()
        cog_deg = calculate_initial_compass_bearing(point1, point2)
        dist_meters = measure_distance_spherical(point1, point2)
        meters_per_sec = dist_meters / (t2 - t1).total_seconds()
        return [cog_deg, meters_per_sec]        

    def compute_future_position(self, current_pos, meters_per_sec, heading_deg, prediction_timedelta):
        heading_rad = radians(heading_deg)
        dist = meters_per_sec * prediction_timedelta.total_seconds()
        lat1_rad = radians(current_pos.y)
        lon1_rad = radians(current_pos.x)
        lat2_rad = asin(sin(lat1_rad) * cos(dist / R_EARTH) + cos(lat1_rad) * 
                    sin(dist / R_EARTH) * cos(heading_rad))
        lon2_rad = lon1_rad + atan2(sin(heading_rad) * sin(dist / R_EARTH) * cos(lat1_rad),
                    cos(dist / R_EARTH) - sin(lat1_rad) * sin(lat2_rad))
        return Point(degrees(lon2_rad),degrees(lat2_rad))
    
    def predict_linearly(self, prediction_timedelta):
        """
        Predicts future positions using linear equations.
        Assumes that input coordinates are in lat/lon.
        """
        current_pos = self.traj.get_end_location()
        [cog_deg, meters_per_sec] = self.calculate_current_cog_and_sog()
        return self.compute_future_position(current_pos, meters_per_sec, cog_deg, prediction_timedelta)

    def predict_kinetically(self, prediction_timedelta):       
        """
        Predicts future positions using kinetic equations.
        Assumes that input coordinates are in lat/lon.
        
        Based on:
        Sang, L. Z., Yan, X. P., Wall, A., Wang, J., & Mao, Z. (2016). CPA calculation method based on AIS position prediction. The Journal of Navigation, 69(6), 1409-1426.
        """
        current_pos = self.traj.get_end_location()
        predict_secs = prediction_timedelta.total_seconds()
        #print("Starting prediction from: {}".format(current_pos))
        
        self.traj.add_heading() 
        self.traj.add_meters_per_sec()
        self.traj.df['prev_heading'] = self.traj.df['heading'].shift()
        self.traj.df['delta_heading'] = self.traj.df['heading'] - self.traj.df['prev_heading'] 
        self.traj.df['prev_ms'] = self.traj.df['meters_per_sec'].shift()
        self.traj.df['delta_ms'] = self.traj.df['meters_per_sec'] - self.traj.df['prev_ms'] 
        self.traj.df.iat[1, self.traj.df.columns.get_loc("delta_heading") ] = self.traj.df.iloc[2]['delta_heading']
        self.traj.df.iat[1, self.traj.df.columns.get_loc("delta_ms") ] = self.traj.df.iloc[2]['delta_ms']
        #print(self.traj.df)
        
        current_heading = float(self.traj.df.tail(1)['heading'])
        current_ms = float(self.traj.df.tail(1)['meters_per_sec'])

        for index, row in self.traj.df.iterrows():
            delta_t_sec = row['delta_t'].total_seconds()
            if delta_t_sec > 0.0:
                #print(row)
                current_heading = current_heading + float(row['delta_heading'])
                current_ms = max(0, current_ms + float(row['delta_ms']))
                #print("COG: {} | SOG: {}".format(current_cog, current_sog))
                scaled_prediction_secs = delta_t_sec * (predict_secs / (self.traj.get_end_time() - self.traj.get_start_time()).total_seconds())    
                current_pos = self.compute_future_position(current_pos, current_ms, current_heading, timedelta(seconds=scaled_prediction_secs))
                #print(current_pos)
        return current_pos          
        
        
        
        