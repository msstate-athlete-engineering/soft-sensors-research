#!/usr/bin/env python3

import glob
import os
import pytz

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.signal as sg

# Input/Output Directories
SRC_DATA_DIR = "../Sample Datasets/Part IX SRS Prototype Validation Study"
DEST_DATA_DIR = "./00-PREPROCESSED-DATA-2"

# Column Naming Constants
MC_COL_NAMES = {"L_Foot_Inversion": "L_IEV", "L_Foot_Flexion": "L_FLX", "R_Foot_Inversion": "R_IEV", "R_Foot_Flexion": "R_FLX"}
MC_TIMEZONE = "US/Central"
SS_L_MAP = ["L_HEEL", "L_EVR", "L_DFX", "L_INV", "L_PFX"]
SS_R_MAP = ["R_PFX", "R_INV", "R_DFX", "R_EVR", "R_HEEL"]

# HOTFIX TRIALS
HOTFIX_TRIMS = {
    "P001_WALK3_BF_L": 615,
    "P002_WALK1_BF_R": 1840,
    "P002_WALK5_SHOE_R": 620,
    "P003_WALK2_BF_L": 680,
    "P003_WALK3_BF_R": 715,
    "P003_WALK4_SHOE_R": 760,
    "P003_WALK6_BF_L": 715,
    "P003_WALK6_SHOE_L": 710,
    "P004_WALK2_SHOE_R": 920,
    "P004_WALK4_SHOE_L": 925,
    "P004_WALK5_SHOE_R": 890,
    "P004_WALK5_SHOE_L": 925,
    "P004_WALK6_SHOE_R": 900,
    "P005_WALK1_SHOE_R": 715,
    "P005_WALK2_SHOE_R": 750,
    "P005_WALK5_BF_R": 730,
    "P005_WALK6_SHOE_R": 770,
    "P006_WALK1_BF_R": 1115,
    "P006_WALK1_BF_L": 1160,
    "P007_WALK2_BF_R": 710,
    "P007_WALK4_SHOE_R": 840,
    "P007_WALK5_BF_R": 860,
    "P007_WALK5_SHOE_R": 800,
    "P008_WALK1_BF_R": 1225,
    "P008_WALK1_BF_L": 1200,
    "P008_WALK2_BF_R": 1265,
    "P008_WALK3_BF_R": 1170,
    "P008_WALK4_BF_R": 1175,
    "P008_WALK5_BF_R": 1175,
    "P009_WALK1_SHOE_R": 950,
    "P009_WALK1_SHOE_L": 900,
    "P009_WALK2_BF_L": 1220,
    "P009_WALK2_SHOE_R": 850,
    "P009_WALK3_BF_R": 1100,
    "P009_WALK3_SHOE_R": 844,
    "P009_WALK6_BF_L": 955,
    "P010_WALK3_BF_L": 925,
    "P010_WALK5_BF_R": 930,
    "P010_WALK5_BF_L": 955,
    "P010_WALK6_SHOE_R": 950
}

# Signal Processing Parameters
ALIGN_WINDOW_LEN = pd.Timedelta(seconds=2.0)
OUTPUT_SAMP_RATE_HZ = 125.0


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


# region 1: Prepare/Combine MC/SS Data #

# 1: a: Auto-detect Trial Names
click.echo("1: a: Auto-detecting trial names... ", nl=False)
MC_FILES = sorted(glob.glob(os.path.join(SRC_DATA_DIR, "*_MC")))
SS_FILES = sorted(glob.glob(os.path.join(SRC_DATA_DIR, "*_SS")))
TRIALS = {os.path.basename(file_path)[:-3] : {} for file_path in MC_FILES + SS_FILES}
click.echo("Done.\n")

# 1: a: i: Sanity check existence of MC and SS file for each trial
for k in TRIALS.keys():
    # Check existence of MC file
    MC_FILE = os.path.join(SRC_DATA_DIR, k + "_MC")
    if not os.path.isfile(MC_FILE):
        raise click.Abort(f"ERROR: Missing MC data for trial {k}. Aborting.")
    else:
        TRIALS[k]["MC_FILE"] = MC_FILE

    # Check existence of SS file
    SS_FILE = os.path.join(SRC_DATA_DIR, k + "_SS")
    if not os.path.isfile(SS_FILE):
        raise click.Abort(f"ERROR: Missing SS data for trial {k}. Aborting.")
    else:
        TRIALS[k]["SS_FILE"] = SS_FILE

# 1: a: ii: Confirm number of trials with user
click.confirm(f"1: a: ii: {len(TRIALS.keys())} trials will be processed. Continue?", abort=True, default=True)

# 1: b: Load MC data for each trial
click.echo("1: b: Load MC Data for Each Trial", nl=False)
for k in TRIALS.keys():
    MC_FILE = TRIALS[k]["MC_FILE"]
    click.echo(f"\n\nLoading {MC_FILE}... ", nl=False)

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
    df = pd.read_csv(MC_FILE, delimiter="\t", skiprows=9, header=0, usecols=lambda x: x in MC_COL_NAMES)
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

    # 1: b: iv: Sanity check columns present and verify with user
    click.echo(f"1: b: iv: Sanity check columns present and verify with user... ", nl=False)
    click.echo(f"Summary of {MC_FILE}:")
    click.echo(f"Timestamp: {epoch}")
    click.echo(f"Sampling Rate: {samp_rate_hz} Hz")
    click.echo(f"Recording Time: {rec_time_s}s")
    df.info()

    # If anomaly in naming detected, confirm with user
    if "R_FLX" not in df.columns or "R_IEV" not in df.columns:  # Check for missing right foot
        raise click.Abort(f"Missing right foot data in file {MC_FILE}.")

    if "WALK" in MC_FILE: # Expect both feet for walking trial
        if "L_FLX" not in df.columns or "L_IEV" not in df.columns: # Check for missing left foot
            raise click.Abort(f"Missing left foot data in {MC_FILE}")
    click.echo("Done.\n")

    # Store DataFrame in TRIALS dictionary
    TRIALS[k]["MC_DATA"] = df

# 1: c: Load SS data for each trial
click.echo("1: c: Load SS Data for Each Trial", nl=False)
for k in TRIALS.keys():
    SS_FILE = TRIALS[k]["SS_FILE"]
    click.echo(f"\n\nLoading {SS_FILE}... ", nl=False)

    # Load file into pandas DataFrame
    df = pd.read_csv(SS_FILE, header=0, index_col=0, date_parser=lambda x: pd.to_datetime(x, unit="us", utc=True))
    click.echo("Done.\n")

    # 1: c: i: Interpolate to reconcile offset indicies
    click.echo(f"1: c: i: Interpolate to reconcile offset indicies... ", nl=False)
    new_idx = pd.date_range(df.index.min(), df.index.max(), freq=f"{1000./OUTPUT_SAMP_RATE_HZ}ms", name="Time")
    df = df.reindex(df.index.union(new_idx)).interpolate("cubic").reindex(new_idx)
    click.echo("Done.\n")

    # 1: c: ii: Round values
    click.echo(f"1: c: ii: Rounding values... ", nl=False)
    df = df.round(decimals=2)
    click.echo("Done.\n")

    # 1: c: iii: Sanity check number of columns based on type of trial
    click.echo(f"1: c: iii: Sanity check number of columns based on type of trial... ", nl=False)
    if len(df.columns) < 5 or ("WALK" in SS_FILE and len(df.columns) < 10):
        raise click.Abort(f"Only {len(df.columns)} imported from {SS_FILE}.")
    click.echo("Done.\n")

    # 1: c: iv: Apply base capacitance layout to auto-rename columns
    click.echo(f"1: c: iv: Apply base capacitance layout to auto-rename columns... ", nl=False)
    col_means = df.mean()
    for i in range(len(col_means) // 5): # Iterate over each set of 5 channels
        min_col = col_means[5 * i : (5 * i) + 5].argmin()
        old_col_names = col_means.index[5 * i : (5 * i) + 5]

        if min_col == SS_L_MAP.index("L_HEEL"): # Check for minimum value on left heel
            df.rename(columns=dict(zip(old_col_names, SS_L_MAP)), inplace=True)
        elif min_col == SS_R_MAP.index("R_HEEL"):    # Check for minimum value on right heel
            df.rename(columns=dict(zip(old_col_names, SS_R_MAP)), inplace=True)
        else:   # Minimum value was in neither expected location
            raise click.Abort(f"Minimum mean value found on channel {min_col}.")

    # HOTFIX P007 MISPATCHED SENSORS
    if "P007" in k:
        df.rename(columns={"R_PFX": "R_INV", "R_INV": "R_EVR", "R_EVR": "R_PFX"}, inplace=True)
    click.echo("Done.\n")

    # Remove left foot from placement trials
    if "WALK" not in SS_FILE and "L_HEEL" in df.columns:
        click.echo("INFO: Left foot data found in placement trial, removing data.")
        df = df[SS_R_MAP]

    # 1: c: v: Sanity check correct feet present based on type of trial
    click.echo(f"1: c: v: Sanity check correct feet present based on type of trial... ", nl=False)
    click.echo(f"Summary of {SS_FILE}:")
    click.echo("Column Means:\n" + str(df.mean()) + "\n")
    df.info()

    # Check for right foot in placement trials, both feet in walking trials
    if "R_HEEL" not in df.columns:
        raise click.Abort("Right foot data not identified in trial.")

    if "WALK" in SS_FILE and "L_HEEL" not in df.columns:
        raise click.Abort("Left foot data not identified in trial.")

    click.echo("Done.\n")

    # Store DataFrame in TRIALS dictionary
    TRIALS[k]["SS_DATA"] = df

# 1: d: Combine MC and SS data to single DataFrame
click.echo("1: d: Combine MC and SS data to single DataFrame.")
for k in TRIALS.keys():
    click.echo(f"Combining MC and SS data for trial {k}... ", nl=False)
    df = pd.merge(TRIALS[k]["MC_DATA"], TRIALS[k]["SS_DATA"], how="outer", left_index=True, right_index=True)
    click.echo("Done.\n")

    df.info()

    # 1: d: i: Interpolate to reconcile offset indicies
    click.echo(f"1: d: i: Interpolate to reconcile offset indicies... ", nl=False)
    new_idx = pd.date_range(df.index.min(), df.index.max(), freq=f"{1000./OUTPUT_SAMP_RATE_HZ}ms", name="Time")
    df = df.reindex(df.index.union(new_idx)).interpolate("cubic").reindex(new_idx)
    click.echo("Done.\n")

    TRIALS[k]["MC_SS_DATA"] = df

# endregion #


# region 2: Align Time-Series Datasets #

for k in TRIALS.keys():
    click.echo(f"\n2: Aligning MC and SS data for trial {k}.")
    mc_ss_data = TRIALS[k]["MC_SS_DATA"].copy()

    for column in mc_ss_data:
        # Low-pass each series
        mc_ss_data[column] = sg.savgol_filter(mc_ss_data[column], 51, 3)
    
    mc_flx = mc_ss_data["R_FLX"]
    mc_iev = mc_ss_data["R_IEV"]
    ss_flx = (mc_ss_data["R_DFX"] - mc_ss_data["R_PFX"])
    ss_iev = (mc_ss_data["R_INV"] - mc_ss_data["R_EVR"])

    mc_flx -= mc_flx.mean(skipna=True)
    mc_iev -= mc_iev.mean(skipna=True)
    ss_flx -= ss_flx.mean(skipna=True)
    ss_iev -= ss_iev.mean(skipna=True)

    mc_max = max(mc_flx.abs().max(skipna=True), mc_iev.abs().max(skipna=True))
    ss_max = max(ss_flx.abs().max(skipna=True), ss_iev.abs().max(skipna=True))
    mc_flx /= mc_max
    mc_iev /= mc_max
    ss_flx /= ss_max
    ss_iev /= ss_max

    mc_flx_var = np.var(mc_flx, ddof=1)
    mc_iev_var = np.var(mc_iev, ddof=1)

    print(f"FLX Variance: {mc_flx_var}, Max: {np.max(mc_flx)}")
    print(f"IEV Variance: {mc_iev_var}, Max: {np.max(mc_iev)}")

    trim = len(mc_flx) - 1
    if mc_flx_var < 0.05 and mc_iev_var < 0.05 or k + "_R" in HOTFIX_TRIMS:
        if k + "_R" not in HOTFIX_TRIMS:
            plt.figure()
            plt.plot(range(len(mc_flx)), mc_flx)
            plt.plot(range(len(mc_iev)), mc_iev)
            plt.show()
            plt.close()

        if k + "_R" in HOTFIX_TRIMS or click.confirm("Variance threshold triggered. Trim file manually?", default=True):
            if k + "_R" in HOTFIX_TRIMS:
                trim = HOTFIX_TRIMS[k + "_R"]
            else:
                trim = click.prompt("Which sample should be the end of this time series?", type=int)
            mc_flx = mc_ss_data["R_FLX"]
            mc_iev = mc_ss_data["R_IEV"]
            mc_flx[trim:] = np.nan
            mc_iev[trim:] = np.nan
            mc_flx -= mc_flx.mean(skipna=True)
            mc_iev -= mc_iev.mean(skipna=True)
            mc_max = max(mc_flx.abs().max(skipna=True), mc_iev.abs().max(skipna=True))
            mc_flx /= mc_max
            mc_iev /= mc_max

        # plt.figure()
        # plt.plot(range(len(mc_flx)), mc_flx)
        # plt.plot(range(len(mc_iev)), mc_iev)
        # plt.show()
        # plt.close()

    flx_xcorr = np.correlate(mc_flx.fillna(value=0.0), ss_flx.fillna(value=0.0), mode="full")
    iev_xcorr = np.correlate(mc_iev.fillna(value=0.0), ss_iev.fillna(value=0.0), mode="full")
    flx_lag = np.argmax(flx_xcorr) - (len(flx_xcorr) // 2)
    iev_lag = np.argmax(iev_xcorr) - (len(flx_xcorr) // 2)
    flx_lag_ms = flx_lag * 8.0
    iev_lag_ms = iev_lag * 8.0

    print(f"FLX Lag: {flx_lag} ({flx_lag_ms}ms), Score: {np.max(flx_xcorr)}")
    print(f"IEV Lag: {iev_lag} ({iev_lag_ms}ms), Score: {np.max(iev_xcorr)}")

    lag_ms = flx_lag if np.max(flx_xcorr) > np.max(iev_xcorr) else iev_lag
    TRIALS[k]["MC_SS_DATA"]["R_DFX"] = TRIALS[k]["MC_SS_DATA"]["R_DFX"].shift(lag_ms)
    TRIALS[k]["MC_SS_DATA"]["R_PFX"] = TRIALS[k]["MC_SS_DATA"]["R_PFX"].shift(lag_ms)
    TRIALS[k]["MC_SS_DATA"]["R_INV"] = TRIALS[k]["MC_SS_DATA"]["R_INV"].shift(lag_ms)
    TRIALS[k]["MC_SS_DATA"]["R_EVR"] = TRIALS[k]["MC_SS_DATA"]["R_EVR"].shift(lag_ms)
    TRIALS[k]["MC_SS_DATA"]["R_HEEL"] = TRIALS[k]["MC_SS_DATA"]["R_HEEL"].shift(lag_ms)

    TRIALS[k]["MC_SS_DATA"]["R_DFX"][trim:] = np.nan
    TRIALS[k]["MC_SS_DATA"]["R_PFX"][trim:] = np.nan
    TRIALS[k]["MC_SS_DATA"]["R_INV"][trim:] = np.nan
    TRIALS[k]["MC_SS_DATA"]["R_EVR"][trim:] = np.nan
    TRIALS[k]["MC_SS_DATA"]["R_HEEL"][trim:] = np.nan

    plt.figure()

    plt.subplot(2, 2, 1)
    plt.plot(mc_flx)
    plt.plot(ss_flx)
    plt.ylabel("FLX PRE")

    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)

    plt.subplot(2, 2, 2)
    plt.plot(mc_iev)
    plt.plot(ss_iev)
    plt.ylabel("IEV PRE")

    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)

    if np.max(flx_xcorr) >= np.max(iev_xcorr):
        plt.subplot(2, 2, 3, facecolor="#dddddd")
    else:
        plt.subplot(2, 2, 3)
    plt.plot(mc_flx)
    plt.plot(ss_flx.index + pd.Timedelta(milliseconds=flx_lag_ms), ss_flx)
    plt.ylabel("FLX POST")

    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)


    if np.max(flx_xcorr) < np.max(iev_xcorr):
        plt.subplot(2, 2, 4, facecolor="#dddddd")
    else:
        plt.subplot(2, 2, 4)
    plt.plot(mc_iev)
    plt.plot(ss_iev.index + pd.Timedelta(milliseconds=iev_lag_ms), ss_iev)
    plt.ylabel("IEV POST")
   
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_visible(False)
    
    plt.savefig(os.path.join(DEST_DATA_DIR, k + "_R.png"))
    plt.close()


    # DO LEFT FOOT FOR WALKING TRIALS
    if "WALK" in k:
        mc_flx = mc_ss_data["L_FLX"]
        mc_iev = mc_ss_data["L_IEV"]
        ss_flx = (mc_ss_data["L_DFX"] - mc_ss_data["L_PFX"])
        ss_iev = (mc_ss_data["L_INV"] - mc_ss_data["L_EVR"])

        mc_flx -= mc_flx.mean(skipna=True)
        mc_iev -= mc_iev.mean(skipna=True)
        ss_flx -= ss_flx.mean(skipna=True)
        ss_iev -= ss_iev.mean(skipna=True)

        mc_max = max(mc_flx.abs().max(skipna=True), mc_iev.abs().max(skipna=True))
        ss_max = max(ss_flx.abs().max(skipna=True), ss_iev.abs().max(skipna=True))
        mc_flx /= mc_max
        mc_iev /= mc_max
        ss_flx /= ss_max
        ss_iev /= ss_max

        mc_flx_var = np.var(mc_flx, ddof=1)
        mc_iev_var = np.var(mc_iev, ddof=1)

        print(f"FLX Variance: {mc_flx_var}, Max: {np.max(mc_flx)}")
        print(f"IEV Variance: {mc_iev_var}, Max: {np.max(mc_iev)}")

        trim = len(mc_flx) - 1
        if mc_flx_var < 0.05 and mc_iev_var < 0.05 or k + "_L" in HOTFIX_TRIMS:
            if k + "_L" not in HOTFIX_TRIMS:
                plt.figure()
                plt.plot(range(len(mc_flx)), mc_flx)
                plt.plot(range(len(mc_iev)), mc_iev)
                plt.show()
                plt.close()

            if k + "_L" in HOTFIX_TRIMS or click.confirm("Variance threshold triggered. Trim file manually?", default=True):
                if k + "_L" in HOTFIX_TRIMS:
                    trim = HOTFIX_TRIMS[k + "_L"]
                else:
                    trim = click.prompt("Which sample should be the end of this time series?", type=int)
                mc_flx = mc_ss_data["L_FLX"]
                mc_iev = mc_ss_data["L_IEV"]
                mc_flx[trim:] = np.nan
                mc_iev[trim:] = np.nan
                mc_flx -= mc_flx.mean(skipna=True)
                mc_iev -= mc_iev.mean(skipna=True)
                mc_max = max(mc_flx.abs().max(skipna=True), mc_iev.abs().max(skipna=True))
                mc_flx /= mc_max
                mc_iev /= mc_max

            # plt.figure()
            # plt.plot(range(len(mc_flx)), mc_flx)
            # plt.plot(range(len(mc_iev)), mc_iev)
            # plt.show()
            # plt.close()

        flx_xcorr = np.correlate(mc_flx.fillna(value=0.0), ss_flx.fillna(value=0.0), mode="full")
        iev_xcorr = np.correlate(mc_iev.fillna(value=0.0), ss_iev.fillna(value=0.0), mode="full")
        flx_lag = np.argmax(flx_xcorr) - (len(flx_xcorr) // 2)
        iev_lag = np.argmax(iev_xcorr) - (len(flx_xcorr) // 2)
        flx_lag_ms = flx_lag * 8.0
        iev_lag_ms = iev_lag * 8.0

        print(f"FLX Lag: {flx_lag} ({flx_lag_ms}ms), Score: {np.max(flx_xcorr)}")
        print(f"IEV Lag: {iev_lag} ({iev_lag_ms}ms), Score: {np.max(iev_xcorr)}")

        lag_ms = flx_lag if np.max(flx_xcorr) > np.max(iev_xcorr) else iev_lag
        TRIALS[k]["MC_SS_DATA"]["L_DFX"] = TRIALS[k]["MC_SS_DATA"]["L_DFX"].shift(lag_ms)
        TRIALS[k]["MC_SS_DATA"]["L_PFX"] = TRIALS[k]["MC_SS_DATA"]["L_PFX"].shift(lag_ms)
        TRIALS[k]["MC_SS_DATA"]["L_INV"] = TRIALS[k]["MC_SS_DATA"]["L_INV"].shift(lag_ms)
        TRIALS[k]["MC_SS_DATA"]["L_EVR"] = TRIALS[k]["MC_SS_DATA"]["L_EVR"].shift(lag_ms)
        TRIALS[k]["MC_SS_DATA"]["L_HEEL"] = TRIALS[k]["MC_SS_DATA"]["L_HEEL"].shift(lag_ms)

        TRIALS[k]["MC_SS_DATA"]["L_DFX"][trim:] = np.nan
        TRIALS[k]["MC_SS_DATA"]["L_PFX"][trim:] = np.nan
        TRIALS[k]["MC_SS_DATA"]["L_INV"][trim:] = np.nan
        TRIALS[k]["MC_SS_DATA"]["L_EVR"][trim:] = np.nan
        TRIALS[k]["MC_SS_DATA"]["L_HEEL"][trim:] = np.nan

        plt.figure()

        plt.subplot(2, 2, 1)
        plt.plot(mc_flx)
        plt.plot(ss_flx)
        plt.ylabel("FLX PRE")

        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_visible(False)

        plt.subplot(2, 2, 2)
        plt.plot(mc_iev)
        plt.plot(ss_iev)
        plt.ylabel("IEV PRE")

        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_visible(False)

        if np.max(flx_xcorr) >= np.max(iev_xcorr):
            plt.subplot(2, 2, 3, facecolor="#dddddd")
        else:
            plt.subplot(2, 2, 3)
        plt.plot(mc_flx)
        plt.plot(ss_flx.index + pd.Timedelta(milliseconds=flx_lag_ms), ss_flx)
        plt.ylabel("FLX POST")

        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_visible(False)


        if np.max(flx_xcorr) < np.max(iev_xcorr):
            plt.subplot(2, 2, 4, facecolor="#dddddd")
        else:
            plt.subplot(2, 2, 4)
        plt.plot(mc_iev)
        plt.plot(ss_iev.index + pd.Timedelta(milliseconds=iev_lag_ms), ss_iev)
        plt.ylabel("IEV POST")
        
        frame1 = plt.gca()
        frame1.axes.get_xaxis().set_visible(False)
        
        plt.savefig(os.path.join(DEST_DATA_DIR, k + "_L.png"))
        plt.close()

    TRIALS[k]["MC_SS_DATA"].to_csv(os.path.join(DEST_DATA_DIR, k + ".csv"))
        

# endregion #
