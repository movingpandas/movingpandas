# -*- coding: utf-8 -*-

"""
***************************************************************************
    sandbox.py
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

import os
import sys 
import unittest
import pandas as pd 
import numpy as np
from geopandas import GeoDataFrame, read_file
from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate
from datetime import datetime, timedelta
from numpy import nan


script_path = os.path.dirname(__file__)
sys.path.append(os.path.join(script_path,".."))

from trajectory import Trajectory 
#from trajectoryPredictor import TrajectoryPredictor

pd.set_option('display.max_colwidth', -1)

data = [{'id':1, 'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
    {'id':1, 'geometry':Point(10,0), 't':datetime(2018,1,1,12,1,0)},
    {'id':1, 'geometry':Point(30,0), 't':datetime(2018,1,1,12,2,0)}]    
df = pd.DataFrame(data).set_index('t')
geo_df = GeoDataFrame(df, crs={'init': '31256'})
traj = Trajectory(1,geo_df)

