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

import warnings
import random
from pandas import NaT
from datetime import timedelta


class TrajectorySample():
    def __init__(self, id, start_timedelta, past_timedelta, future_timedelta, past_traj, future_pos):
        self.id = id
        self.start_secs = start_timedelta.total_seconds()
        self.past_secs = past_timedelta.total_seconds()
        self.future_secs = future_timedelta.total_seconds()
        self.past_traj = past_traj
        self.future_pos = future_pos
        
    def __str__(self):
        return "{};{};{};{};{};{}".format(
            self.id, self.start_secs, self.past_secs, self.future_secs, self.past_traj.to_linestring().wkt, self.future_pos.wkt)


class TrajectorySampler():
    def __init__(self, traj, tolerance = timedelta(seconds=1)):
        self.traj = traj
        self.sample_counter = 0
        self.tolerance = tolerance 
        
    def is_sampling_possible(self, past_timedelta, future_timedelta, min_meters_per_sec = 0.3):
        sample_duration = past_timedelta + future_timedelta 
        if self.traj.get_duration() < sample_duration:
            raise RuntimeError("Trajectory {} is too short to extract sample of {} seconds!".format(
                self.traj.id, sample_duration.total_seconds()))
        
        self.traj.add_meters_per_sec() 
        self.traj.df['next_ms'] = self.traj.df['meters_per_sec'].shift(-1)
        self.traj.df = self.traj.df[:-1]

        above_speed_limit = self.traj.df[self.traj.df['next_ms'] > min_meters_per_sec]
        if len(above_speed_limit) == 0:
            raise RuntimeError("No data above specified speed limit!")
        
        return True 
        
    def is_sampling_successful(self, start_time, past_time, future_time):
        sample_times = []
        for t in [start_time, past_time, future_time]:
            #print("Testing {}".format(t))
            row = self.traj.get_row_at(t)
            if abs(row['t'] - t) > self.tolerance: 
                return False
            else:
                sample_times.append(row['t'])    
        return sample_times
        
    def get_sample_times(self, df, delta_t, first_move_time, past_timedelta, future_timedelta, randomize):
        for t, row in df.iterrows():
            if randomize:
                if t < first_move_time + delta_t:
                    continue
            delta_t += row['delta_t']
            #print(delta_t)
            start_time = self.traj.get_row_at(first_move_time + past_timedelta + delta_t)['t']
            start_timedelta = start_time - first_move_time
            past_time = start_time - past_timedelta
            future_time = start_time + future_timedelta   
            x = self.is_sampling_successful(start_time, past_time, future_time)
            if x: 
                #print('OK')
                start_time, past_time, future_time = x     
                successful = True
                return successful, start_time, past_time, future_time, start_timedelta
              
    def get_sample(self, past_timedelta, future_timedelta, min_meters_per_sec = 0.3, randomize = False):
        number_of_retries = 3
        if not self.is_sampling_possible(past_timedelta, future_timedelta, min_meters_per_sec):
            raise RuntimeError("Cannot extract sample from this trajectory!")
        
        above_speed_limit = self.traj.df[self.traj.df['next_ms'] > min_meters_per_sec]
        first_move_time = above_speed_limit.index.min().to_pydatetime()
        
        df = self.traj.df[self.traj.df.index >= first_move_time]
        df.iat[0, df.columns.get_loc("delta_t")] = timedelta(seconds=0)
        
        successful = False
        if randomize:
            while not successful and number_of_retries > 0:
                random_start = random.randint(0, int((self.traj.get_duration()-future_timedelta).total_seconds()))
                delta_t = timedelta(seconds=random_start)
                sample_times = self.get_sample_times(df, delta_t, first_move_time, past_timedelta, future_timedelta, randomize)
                if sample_times:
                    successful, start_time, past_time, future_time, start_timedelta = sample_times
                number_of_retries -= 1
        else:
            delta_t = timedelta(seconds=0)
            sample_times = self.get_sample_times(df, delta_t, first_move_time, past_timedelta, future_timedelta, randomize)
            if sample_times:
                successful, start_time, past_time, future_time, start_timedelta = sample_times
             
        if not successful:
            raise RuntimeError("Failed to extract sample from trajectory {}!".format(self.traj.id))
             
        future_pos = self.traj.get_position_at(future_time)
        
        past_traj = self.traj.get_segment_between(past_time, start_time)
        #if not past_traj:
        #    raise RuntimeError("Failed to extract past trajectory!")

        sample_id = "{}_{}".format(self.traj.id, self.sample_counter)
        self.sample_counter += 1
        return TrajectorySample(sample_id, start_timedelta, past_timedelta, future_timedelta, past_traj, future_pos)
        
        
    