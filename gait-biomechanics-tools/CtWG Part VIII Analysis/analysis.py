#!/usr/bin/env python3

import glob
import itertools
import os
import pytz

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.signal as sg

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Input/Output Directories
SRC_DATA_DIR = "./AlanaDISDataPreprocessed"

# Trial Names
PARTICIPANTS = [f"P{'{:0>3}'.format(n)}" for n in range(1, 17)]  # P001 .. P016
TRIALS = ["FLEX", "SQUAT", "WALK1", "WALK2", "WALK3", "WALK4", "WALK5", "WALK6"]

print("PARTICIPANT\tTRIAL\tR^2\tRMSE\tMAE")
for participant, trial in itertools.product(PARTICIPANTS, TRIALS):
    if not os.path.exists(os.path.join(SRC_DATA_DIR, f"{participant}_{trial}.csv")):
        print(f"{participant}\t{trial}\t-\t-\t-")
        continue

    df = pd.read_csv(os.path.join(SRC_DATA_DIR, f"{participant}_{trial}.csv"), header=0, index_col=0, parse_dates=True)
    for col in df:
        df[col] = sg.savgol_filter(df[col], 31, 3)
    
    X = df["Channel 0"].to_numpy().reshape(-1, 1)
    y = df["R_KNEE_FLX"].to_numpy()
    reg = LinearRegression().fit(X, y)

    r2_score = reg.score(X, y)
    rmse_score = mean_squared_error(y, reg.predict(X), squared=False)
    mae_score = mean_absolute_error(y, reg.predict(X))

    print(f"{participant}\t{trial}\t{r2_score}\t{rmse_score}\t{mae_score}")