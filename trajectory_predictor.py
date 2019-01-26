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

from math import sin, cos, atan2, radians, degrees, asin
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
        start_prediction_from = self.traj.get_end_location()
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

        # total time range between first and last point in trajectory
        time_range = self.traj.get_end_time() - self.traj.get_start_time()
        # distances in x- and y-direction that will be added to the last point of the trajectory
        dx = 0.0
        dy = 0.0

        # loop over all historic points
        for index, row in self.traj.df.iterrows():

            # only proceed if delta_t > 0, because otherwise division through zero will occur
            delta_t_sec = row['delta_t'].total_seconds()
            if delta_t_sec > 0.0:
                # calculate COG based on ROT
                current_heading = current_heading + float(row['delta_heading'])
                # calculate SOG based on COS
                current_ms = max(0, current_ms + float(row['delta_ms']))
                # calculate the prediction time for this point (i.e., how much of the prediction is explained by this pair of points)
                prediction_time = prediction_timedelta.total_seconds() * (delta_t_sec / time_range)
                # predict into the future, starting from the last point of the trajectory
                predicted_pos = self.compute_future_position(start_prediction_from, current_ms, current_heading, timedelta(seconds=prediction_time))
                # store the differences in x- and y-direction (this is what this point adds to the prediction)
                dx += radians(predicted_pos.x() - start_prediction_from.x())
                dy += radians(predicted_pos.y() - start_prediction_from.y())

        # add distances in x- and y-direction to the last point of the trajectory
        predicted_x = radians(start_prediction_from.x()) + dx
        predicted_y = radians(start_prediction_from.y()) + dy
        # save predicted point
        predicted_point = Point(degrees(predicted_x), degrees(predicted_y))
        return predicted_point
        