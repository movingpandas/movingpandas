# -*- coding: utf-8 -*-

"""
***************************************************************************
    trajectory_sampler.py
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

import random
from datetime import timedelta
from shapely.geometry import Point

from geometry_utils import measure_distance_spherical


class TrajectorySample():
    def __init__(self, id, start_timedelta, past_timedelta, future_timedelta, past_traj, future_pos, future_traj):
        self.id = id
        self.start_secs = start_timedelta.total_seconds()
        self.past_secs = past_timedelta.total_seconds()
        self.future_secs = future_timedelta.total_seconds()
        self.past_traj = past_traj
        self.future_pos = future_pos
        self.future_traj = future_traj
        
    def __str__(self):
        return "{};{};{};{};{};{};{}".format(
            self.id, self.start_secs, self.past_secs, self.future_secs, self.past_traj.to_linestring().wkt, 
            self.future_pos.wkt, self.future_traj.to_linestring().wkt)


class TrajectorySampler():
    def __init__(self, traj, tolerance = timedelta(seconds=1)):
        self.traj = traj
        self.sample_counter = 0
        self.tolerance = tolerance 
        
    def _is_sampling_possible(self, past_timedelta, future_timedelta, min_meters_per_sec = 0.3):
        sample_duration = past_timedelta + future_timedelta 
        if self.traj.get_duration() < sample_duration:
            raise RuntimeError("Trajectory {} is too short to extract {} seconds sample!".format(
                self.traj.id, sample_duration.total_seconds()))
        
        self.traj.add_meters_per_sec() 
        self.traj.df['next_ms'] = self.traj.df['meters_per_sec'].shift(-1)
        self.traj.df = self.traj.df[:-1]

        above_speed_limit = self.traj.df[self.traj.df['next_ms'] > min_meters_per_sec]
        if len(above_speed_limit) == 0:
            raise RuntimeError("No data above specified speed limit!")
        
        return True 
        
    def _is_sampling_successful(self, start_time, past_time, future_time):
        sample_times = []
        for t in [start_time, past_time, future_time]:
            #print("Testing {}".format(t))
            row = self.traj.get_row_at(t)
            if abs(row['t'] - t) > self.tolerance: 
                return False
            else:
                sample_times.append(row['t'])    
        return sample_times
        
    def _get_sample_times(self, df, delta_t, first_move_time, past_timedelta, future_timedelta, randomize):
        for t, row in df.iterrows():
            if t > self.traj.get_end_time() - (past_timedelta + future_timedelta):
                continue
            if randomize:
                if t < first_move_time + delta_t:
                    continue
            delta_t += row['delta_t']
            #print(delta_t)
            start_time = self.traj.get_row_at(first_move_time + past_timedelta + delta_t)['t']
            start_timedelta = start_time - first_move_time
            past_time = start_time - past_timedelta
            future_time = start_time + future_timedelta   
            x = self._is_sampling_successful(start_time, past_time, future_time)
            if x: 
                #print('OK')
                start_time, past_time, future_time = x     
                successful = True
                return successful, start_time, past_time, future_time, start_timedelta
        raise RuntimeError('Failed to get sample times! ')
                
    def _get_time_of_first_move(self, min_meters_per_sec):
        above_speed_limit = self.traj.df[self.traj.df['next_ms'] > min_meters_per_sec]
        return above_speed_limit.index.min().to_pydatetime()
        
    def _filter_df(self, first_move_time):
        df = self.traj.df[self.traj.df.index >= first_move_time]
        df.iat[0, df.columns.get_loc("delta_t")] = timedelta(seconds=0)
        return df
        
    def _match_sample_pattern_to_df(self, df, first_move_time, past_timedelta, future_timedelta, randomize):
        if randomize:
            number_of_retries = 3
            random_start = random.randint(0, int((self.traj.get_duration() - future_timedelta).total_seconds()))
            delta_t = timedelta(seconds=random_start)
        else:
            number_of_retries = 1
            delta_t = timedelta(seconds=0)
        successful = False
        while not successful and number_of_retries > 0:
            try:
                successful, start_time, past_time, future_time, start_timedelta = self._get_sample_times(
                    df, delta_t, first_move_time, past_timedelta, future_timedelta, randomize)
            except RuntimeError:
                number_of_retries -= 1
                random_start = random.randint(0, int((self.traj.get_duration() - future_timedelta).total_seconds()))
                delta_t = timedelta(seconds=random_start)

        if not successful:
            raise RuntimeError("Failed to extract sample from trajectory {}!".format(self.traj.id))
        return successful, start_time, past_time, future_time, start_timedelta
    
    def _is_moving_sufficiently(self, traj, min_meters_per_sec, past_timedelta):
        line_coords = traj.to_linestring().coords
        covered_distance = measure_distance_spherical(Point(line_coords[0]), Point(line_coords[-1]))
        if covered_distance < 0.5 * min_meters_per_sec * past_timedelta.total_seconds():
            return False
        else:
            return True
          
    def get_sample(self, past_timedelta, future_timedelta, min_meters_per_sec=0.3, randomize=False, future_traj_duration=timedelta(hours=0)):      
        if not self._is_sampling_possible(past_timedelta, future_timedelta, min_meters_per_sec):
            raise RuntimeError("Cannot extract sample from this trajectory!")
        
        first_move_time = self._get_time_of_first_move(min_meters_per_sec)
        df = self._filter_df(first_move_time)
        
        successful, start_time, past_time, future_time, start_timedelta = self._match_sample_pattern_to_df(
            df, first_move_time, past_timedelta, future_timedelta, randomize)

        future_pos = self.traj.get_position_at(future_time)
        past_traj = self.traj.get_segment_between(past_time, start_time)
        
        if self.traj.has_parent():
            future_traj = self.traj.parent.get_segment_between(start_time, start_time + future_traj_duration)
        else:
            future_traj = self.traj.get_segment_between(start_time, start_time + future_traj_duration)
        
        if not self._is_moving_sufficiently(past_traj, min_meters_per_sec, past_timedelta):
            raise RuntimeError("Skipping sample {} since it there is not enough movement!".format(self.traj.id))

        self.sample_counter += 1
        sample_id = "{}_{}".format(self.traj.id, self.sample_counter)        
        return TrajectorySample(sample_id, start_timedelta, past_timedelta, future_timedelta, past_traj, future_pos, future_traj)
        
        
    