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

# Input/Output Directories
SRC_DATA_DIR = "./AlanaDISData"
DEST_DATA_DIR = "./AlanaDISDataPreprocessed"

# Trial Names
PARTICIPANTS = [f"P{'{:0>3}'.format(n)}" for n in range(1, 17)]  # P001 .. P016
TRIALS = ["FLEX", "SQUAT", "WALK1", "WALK2", "WALK3", "WALK4", "WALK5", "WALK6"]

# File Column Names
MC_COL_NAMES = {"Right_Leg_Flexion": "R_KNEE_FLX"}
MC_TIMEZONE = "US/Central"
OUTPUT_SAMP_RATE_HZ = 250.0

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


# region 1: Load Experiment Data per Trial #

EXP_DATA = {}
for participant, trial in itertools.product(PARTICIPANTS, TRIALS):
    EXP_DATA[f"{participant}_{trial}"] = {}

    MC_FILE = f"{SRC_DATA_DIR}/{participant}_{trial}"
    SS_FILE = f"{SRC_DATA_DIR}/StretchSense/{participant}_{trial}.csv"

    if not os.path.exists(MC_FILE):
        click.echo(f"Missing {MC_FILE}. Skipping trial...")
        continue

    if not os.path.exists(SS_FILE):
        click.echo(f"Missing {SS_FILE}. Skipping trial...")
        continue

    # Load metadata from file header
    for i, line in enumerate(open(MC_FILE)):
        if i == 2:  # Read recording timestamp
            time_str = " ".join(line.split("\t")[1:3])
            epoch = pd.to_datetime(time_str, format="%d-%m-%Y %H:%M:%S:%f")
            epoch = pytz.timezone(MC_TIMEZONE).localize(epoch, is_dst=None).astimezone(pytz.UTC)
        if i == 3:  # Read recording sampling rate
            samp_rate_hz = float(line.split("\t")[0])
            secs_per_samp = 1. / samp_rate_hz
        if i == 4:  # Read recording data capture period
            rec_time_s = float(line.split("\t")[0])

    # Load file into pandas DataFrame and print basic info
    df = pd.read_csv(MC_FILE, delimiter="\t", skiprows=8, header=0, usecols=lambda x: x in MC_COL_NAMES)
    click.echo("Done.\n")

    # 1: b: i: Use header data to generate DatetimeIndex
    click.echo(f"1: b: i: Generating DatetimeIndex... ", nl=False)
    df.index = pd.date_range(epoch, epoch + pd.Timedelta(seconds=rec_time_s), freq=f"{secs_per_samp}S", name="Time")
    click.echo("Done.\n")

    # 1: b: ii/iii: Assign standard column names and round values
    click.echo(f"1: b: ii/iii: Renaming columns and rounding values... ", nl=False)
    df = df.rename(columns=MC_COL_NAMES)
    df = df.round(decimals=2)
    click.echo("Done.\n")

    EXP_DATA[f"{participant}_{trial}"]["MOCAP"] = df

    # Load file into pandas DataFrame
    df = pd.read_csv(SS_FILE, header=0, index_col=0, date_parser=lambda x: pd.to_datetime(x, unit="us", utc=True), usecols=lambda x: "0" in x)
    click.echo("Done.\n")

    # 1: c: ii: Round values
    click.echo(f"1: c: ii: Rounding values... ", nl=False)
    df = df.round(decimals=2)
    click.echo("Done.\n")

    EXP_DATA[f"{participant}_{trial}"]["STRETCHSENSE"] = df



    df = pd.merge(EXP_DATA[f"{participant}_{trial}"]["MOCAP"], EXP_DATA[f"{participant}_{trial}"]["STRETCHSENSE"], how="outer", left_index=True, right_index=True)
    new_idx = pd.date_range(df.index.min(), df.index.max(), freq=f"{1000./OUTPUT_SAMP_RATE_HZ}ms", name="Time")
    df = df.reindex(df.index.union(new_idx)).interpolate("cubic").reindex(new_idx)
    EXP_DATA[f"{participant}_{trial}"] = df.copy()

    # Cross correlate
    for column in df:
        # Low-pass each series
        df[column] = sg.savgol_filter(df[column], 51, 3)

    mc_flx = df["R_KNEE_FLX"]  
    ss_flx = df["Channel 0"]

    mc_flx[int(len(mc_flx.dropna()) * 0.75):] = np.nan
    ss_fvi = ss_flx.reset_index(drop=True).first_valid_index()
    ss_flx[ss_fvi + len(mc_flx.dropna()):] = np.nan

    mc_flx -= mc_flx.mean(skipna=True)
    ss_flx -= ss_flx.mean(skipna=True)

    # mc_flx /= mc_flx.abs().max(skipna=True)
    # ss_flx /= ss_flx.abs().max(skipna=True)

    mc_flx /= np.std(mc_flx)
    ss_flx /= np.std(ss_flx)

    flx_xcorr = np.correlate(mc_flx.fillna(value=0.0), ss_flx.fillna(value=0.0), mode="full")
    flx_lag = np.argmax(flx_xcorr) - (len(flx_xcorr) // 2)
    flx_lag_ms = int(flx_lag * (1000. / OUTPUT_SAMP_RATE_HZ))

    EXP_DATA[f"{participant}_{trial}"]["Channel 0"] = EXP_DATA[f"{participant}_{trial}"]["Channel 0"].shift(flx_lag)
    EXP_DATA[f"{participant}_{trial}"].dropna(how="any", inplace=True)

    X = EXP_DATA[f"{participant}_{trial}"]["Channel 0"].to_numpy().reshape(-1, 1)
    y = EXP_DATA[f"{participant}_{trial}"]["R_KNEE_FLX"].to_numpy()
    reg = LinearRegression().fit(X, y)

    if reg.score(X, y) < 0.9:
        plt.figure()
        plt.plot(EXP_DATA[f"{participant}_{trial}"]["R_KNEE_FLX"].reset_index(drop=True))
        plt.plot(EXP_DATA[f"{participant}_{trial}"]["Channel 0"].reset_index(drop=True))
        plt.grid()
        plt.legend(["MOCAP", "SS"])
        plt.xlabel("Time (samples)")
        plt.show()
        plt.close()
        
        trimval = click.prompt("Which sample should be the end of this time series?", type=int)
        if trimval != 0:
            EXP_DATA[f"{participant}_{trial}"] = EXP_DATA[f"{participant}_{trial}"][:trimval]

    EXP_DATA[f"{participant}_{trial}"].to_csv(os.path.join(DEST_DATA_DIR, f"{participant}_{trial}" + ".csv"))

    # plt.figure()

    # plt.subplot(2, 1, 1)
    # plt.plot(mc_flx)
    # plt.plot(ss_flx)
    # plt.ylabel("FLX PRE")

    # frame1 = plt.gca()
    # frame1.axes.get_xaxis().set_visible(False)

    # plt.subplot(2, 1, 2)
    # plt.plot(mc_flx)
    # plt.plot(ss_flx.index + pd.Timedelta(milliseconds=flx_lag_ms), ss_flx)
    # plt.ylabel("FLX POST")

    # frame1 = plt.gca()
    # frame1.axes.get_xaxis().set_visible(False)
    
    # plt.savefig(os.path.join(DEST_DATA_DIR, f"{participant}_{trial}" + ".png"))
    # plt.close()



# endregion #


