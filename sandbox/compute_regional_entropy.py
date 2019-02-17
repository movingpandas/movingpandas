# -*- coding: utf-8 -*-

"""
***************************************************************************
    compute_regional_entropy.py
    ---------------------
    Date                 : February 2019
    Copyright            : (C) 2019 by Anita Graser
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

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import entropy
from geopandas import read_file, sjoin
from shapely.geometry import Polygon
from datetime import datetime

script_path = os.path.dirname(__file__)
sys.path.append(os.path.join(script_path, ".."))

from trajectory import Trajectory

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_columns', 500)

INPUT_REGIONS = os.path.join(script_path, '../demo/demodata_grid_fine.gpkg')
REGION_ID = 'id'
INPUT_MOVEMENT = os.path.join(script_path,'../demo/demodata_geolife_large.gpkg')
TRAJECTORY_ID = 'trajectory_id'
OUTPUT_FILE = os.path.join(script_path,'../demo/tmp_grid_entropy.gpkg')


def prepare_regions(data_path):
    return read_file(data_path)


def prepare_trajectories(data_path, trajectory_id, regions):
    df = read_file(data_path)
    df['t'] = pd.to_datetime(df['t'])
    df = df.set_index('t')
    pts_with_region = sjoin(df, regions, how="inner", op='intersects')
    trajectories = []
    for key, values in pts_with_region.groupby([trajectory_id]):
        trajectory = Trajectory(key, values)
        trajectory.add_heading()
        trajectory.add_meters_per_sec()
        print(trajectory)
        trajectories.append(trajectory)
    return trajectories


def merge_trajectory_dfs_by_region(trajectories, region_id):
    region_values = {}
    for traj in trajectories:
        datas = {}
        for i, g in traj.df.groupby(region_id):
            datas.update({i: g.reset_index(drop=True)})
        for key, value in datas.items():
            if key in region_values.keys():
                region_values[key] += value['heading'].values.tolist()
            else:
                region_values[key] = value['heading'].values.tolist()
    return region_values


def get_entropy(values, n=36):
    # Shannon entropy of directions H_d
    counts = count_and_merge(n, values)
    return entropy(counts)


def count_and_merge(n, bearings):
    # code from https://github.com/gboeing/osmnx-examples/blob/master/notebooks/17-street-network-orientations.ipynb
    # make twice as many bins as desired, then merge them in pairs
    # prevents bin-edge effects around common values like 0° and 90°
    n = n * 2
    bins = np.arange(n + 1) * 360 / n
    count, _ = np.histogram(bearings, bins=bins)
    # move the last bin to the front, so eg 0.01° and 359.99° will be binned together
    count = np.roll(count, 1)
    return count[::2] + count[1::2]


def get_hd(row):
    print(row)
    id = row[REGION_ID]
    if id in HD_VALUES.keys():
        return HD_VALUES[id]
    else:
        return None


if __name__ == '__main__':
    t_start = datetime.now()
    regions = prepare_regions(INPUT_REGIONS)
    trajectories = prepare_trajectories(INPUT_MOVEMENT, TRAJECTORY_ID, regions)
    if REGION_ID in trajectories[0].df.keys():
        joined_id = REGION_ID
    else:
        joined_id = REGION_ID+'_right'
    regions_with_values = merge_trajectory_dfs_by_region(trajectories, joined_id)
    HD_VALUES = {}
    for region, values in regions_with_values.items():
        Hd = get_entropy(values)
        HD_VALUES[region] = Hd
    regions['Hd'] = regions.apply(get_hd, axis=1)
    print(regions)
    regions.to_file(OUTPUT_FILE, driver="GPKG")
    print("Finished in {}".format(datetime.now() - t_start))
