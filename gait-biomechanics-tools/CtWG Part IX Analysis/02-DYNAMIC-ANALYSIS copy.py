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

SRC_DATA_DIR = "./00-PREPROCESSED-DATA"
DEST_DATA_DIR = "./01-DYNAMIC-ANALYSIS"

PARTICIPANTS = ["P001", "P002", "P003", "P004", "P005", "P006", "P007", "P008", "P009", "P010"]
TRIALS = ["WALK1", "WALK2", "WALK3", "WALK4", "WALK5", "WALK6"]
CONFIGURATIONS = ["BF", "SHOE"]

MEAS_MAP = {
    "L_FLX": ["L_PFX", "L_DFX", "L_INV", "L_EVR"],
    "L_IEV": ["L_PFX", "L_DFX", "L_INV", "L_EVR"],
    "R_FLX": ["R_PFX", "R_DFX", "R_INV", "R_EVR"],
    "R_IEV": ["R_PFX", "R_DFX", "R_INV", "R_EVR"]
}


# PRE: a: Create destination director if it doesn't exist
click.echo(f"PRE: a: Creating destination directory {DEST_DATA_DIR}... ", nl=False)
os.makedirs(DEST_DATA_DIR, exist_ok=True)
click.echo("Done.\n")

# PRE: b: If it exists and isn't empty, ask to empty it or abort
existing_files = glob.glob(os.path.join(DEST_DATA_DIR, "**"))
if len(existing_files) != 0:
    click.confirm("PRE: b: Data output directory must be empty. Empty it now?", abort=True, default=False)
    click.echo("Deleting files... ", nl=False)
    for existing_file in existing_files:
        os.remove(existing_file)
    click.echo("Done.\n")

# endregion #


# region 1: Generate Linear Model #

total = 0
total_num = 0

for p in PARTICIPANTS:
    for c in CONFIGURATIONS:
        for meas in ["L_FLX", "L_IEV", "R_FLX", "R_IEV"]:
            X = None
            y = None

            for t in TRIALS:
                mc_ss_data = pd.read_csv(os.path.join(SRC_DATA_DIR, f"{p}_{t}_{c}.csv"), header=0, index_col=0, parse_dates=True)
                mc_ss_data.dropna(how="any", inplace=True)
                mc_ss_data = mc_ss_data[:int(len(mc_ss_data)*0.85)]

                for column in mc_ss_data:
                    mc_ss_data[column] = sg.savgol_filter(mc_ss_data[column], 31, 3)  # 6.9 Hz cutoff @ 125 Hz sampling rate (L = 25)
                
                if X is None:
                    X = mc_ss_data[MEAS_MAP[meas]].to_numpy()
                else:
                    X = np.append(X, mc_ss_data[MEAS_MAP[meas]].to_numpy(), axis=0)
                
                if y is None:
                    y = mc_ss_data[meas].to_numpy()
                else:
                    y = np.append(y, mc_ss_data[meas].to_numpy(), axis=0)

            reg = LinearRegression().fit(X, y)
            adj_r2 = 1 - (1-reg.score(X, y))*(len(y)-1)/(len(y)-X.shape[1]-1)
            total += adj_r2
            total_num += 1

print(f"AVG: {total / total_num}")

# endregion #
