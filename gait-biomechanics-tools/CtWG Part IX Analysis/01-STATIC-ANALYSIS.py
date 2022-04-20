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
from sklearn.metrics import mean_squared_error

SRC_DATA_DIR = "./00-PREPROCESSED-DATA"
DEST_DATA_DIR = "./01-STATIC-ANALYSIS"

PARTICIPANTS = ["P001", "P002", "P003", "P004", "P005", "P006", "P007", "P008", "P009", "P010"]
MOVEMENTS = ["PF", "DF", "INV", "EVR"]
CONFIGURATIONS = ["BF", "SHOE"]

MOVEMENT_MAP = {
    "PF": ("R_PFX", "R_FLX"),
    "DF": ("R_DFX", "R_FLX"),
    "INV": ("R_INV", "R_IEV"),
    "EVR": ("R_EVR", "R_IEV")
}

# MOVEMENT_MAP = {
#     "PF": (["R_PFX", "R_DFX", "R_INV", "R_EVR"], "R_FLX"),
#     "DF": (["R_PFX", "R_DFX", "R_INV", "R_EVR"], "R_FLX"),
#     "INV": (["R_PFX", "R_DFX", "R_INV", "R_EVR"], "R_IEV"),
#     "EVR": (["R_PFX", "R_DFX", "R_INV", "R_EVR"], "R_IEV")
# }

# region PRE: Prepare Destination Directory #

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

for p in PARTICIPANTS:
    for score in ["R^2", "RMSE"]:
        print(f"{p}\t\t", end="")
        for c in CONFIGURATIONS:
            for m in MOVEMENTS:
                mc_ss_data = pd.read_csv(os.path.join(SRC_DATA_DIR, f"{p}_{m}_{c}.csv"), header=0, index_col=0, parse_dates=True)
                mc_ss_data.dropna(how="any", inplace=True)

                for column in mc_ss_data:
                    mc_ss_data[column] = sg.savgol_filter(mc_ss_data[column], 15, 3)  # 15 Hz cutoff @ 125 Hz sampling rate

                X = mc_ss_data[MOVEMENT_MAP[m][0]].to_numpy().reshape(-1, 1)
                y = mc_ss_data[MOVEMENT_MAP[m][1]].to_numpy()
                reg = LinearRegression().fit(X, y)

                if score == "R^2":
                    print(f"{reg.score(X, y)}\t", end="")
                else:
                    print(f"{mean_squared_error(y, reg.predict(X), squared=False)}\t", end="")

                # if reg.score(X, y) < 0.8:
                #     plt.subplot(2,1,1)
                #     plt.plot(mc_ss_data[MOVEMENT_MAP[m][0]])
                #     plt.subplot(2,1,2)
                #     plt.plot(mc_ss_data[MOVEMENT_MAP[m][1]])
                #     plt.show()
            print("\t", end="")
        print("\n", end="")

# endregion #
