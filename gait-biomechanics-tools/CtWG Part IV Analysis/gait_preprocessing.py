#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""Gait study preprocessing file.

"""
from functools import reduce

import pandas as pd
import os
import glob
import preprocessing_utils as proc_utils
from sklearn.preprocessing import scale
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('ggplot')
plt.rcParams["axes.labelsize"] = 10
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["lines.linewidth"] = 0.75


def main():
    """Gait study preprocessing script.
    
    This script performs the preprocessing and visualization of data collected in the
    gait study. 
    """

    saveOutput = False

    moCapHz = 200.0 # Adjust this based on recording rate of motion capture system

    delayTable = pd.DataFrame(columns=['Trial', 'Foot', 'Delay'])

    # Labeling to match up correct files
    lut_sensor = [["R Ankle Flexion",   "SSRightPF",   "MCRightPF"],
        ["R Foot Inversion",  "SSRightINV",  "MCRightINV"],
        ["R Ankle Flexion",   "SSRightDF",   "MCRightDF"],
        ["R Foot Inversion",  "SSRightEVR",  "MCRightEVR"],
        ["L Ankle Flexion",   "SSLeftPF",    "MCLeftPF"],
        ["L Foot Inversion",  "SSLeftINV",   "MCLeftINV"],
        ["L Ankle Flexion",   "SSLeftDF",    "MCLeftDF"],
        ["L Foot Inversion",  "SSLeftEVR",   "MCLeftEVR"]]

    sensorNameLookUpTable = pd.DataFrame(lut_sensor, columns=['MC', 'SS', 'MCRevised'])

    # Load up files from dataset
    # This path must be updated to the directory that contains your participant folders
    participantsPath = os.getcwd() + "/../motionanalyzr/Sample Datasets/SRS Gait Study/"
    participantsFolders = os.listdir(participantsPath)

    lut_trial = [["Walk1.csv", "WALK01.exp"],
                ["Walk2.csv", "WALK02.exp"],
                ["Walk3.csv", "WALK03.exp"],
                ["Walk4.csv", "WALK04.exp"],
                ["Walk5.csv", "WALK05.exp"],
                ["Walk6.csv", "WALK06.exp"],
                ["LeftINV01.csv", "LFT_INV01.exp"],
                ["LeftINV02.csv", "LFT_INV02.exp"],
                ["LeftINV03.csv", "LFT_INV03.exp"],
                ["RightINV01.csv", "RT_INV01.exp"],
                ["RightINV02.csv", "RT_INV02.exp"],
                ["RightINV03.csv", "RT_INV03.exp"]]
    trialLookupTable = pd.DataFrame(lut_trial, columns=['StretchSenseName', 'MoCapName'])

    ssColNames = ["Sequence", "Sample Number", "Time", "Sensor1", "Sensor2", "Sensor3", \
                  "Sensor4", "Sensor5", "Sensor6", "Sensor7", "Sensor8", "Sensor9", \
                  "Sensor10", "Sensor11", "Sensor12", "Sensor13", "Sensor14", "Sensor15", \
                  "Sensor16", "Sensor17", "Sensor18", "Sensor19", "Sensor20"]

    for participantID in participantsFolders:
        SSFiles = glob.glob(participantsPath + participantID + '/StretchSense/*.csv')

        # Create directories to hold reformatted data outputs
        preprocessedGraphDir = participantsPath + participantID + "/Preprocessed Graphs/"
        if not os.path.exists(preprocessedGraphDir):
            os.mkdir(preprocessedGraphDir)

        preprocessedDataDir = participantsPath + participantID + "/Preprocessed Data/"
        if not os.path.exists(preprocessedDataDir):
            os.mkdir(preprocessedDataDir)

        for SSFilename in SSFiles:
            
            SS = pd.read_csv(SSFilename, skiprows=1, names=ssColNames, \
                             usecols=list(range(len(ssColNames))))

            # Trick to remove SPI channels that weren't recorded, i.e. have all zeroes
            SS = SS.loc[:, (SS != 0).any(axis=0)]

            # Conditional statement based on which Module was connected first
            # Right foot module connects first
            if "Sensor1" in SS.columns:
                SS = SS.rename(columns={"Sensor1" : "SSRightPF", "Sensor2" : "SSRightINV",
                                        "Sensor3" : "SSRightDF", "Sensor4" : "SSRightEVR",
                                        "Sensor17" : "SSLeftPF", "Sensor18" : "SSLeftINV",
                                        "Sensor19" : "SSLeftDF", "Sensor20" : "SSLeftEVR"})
            elif "Sensor11" in SS.columns:
                SS = SS.rename(columns={"Sensor11" : "SSRightPF", "Sensor12" : "SSRightINV",
                                        "Sensor13" : "SSRightDF", "Sensor14" : "SSRightEVR",
                                        "Sensor7" : "SSLeftPF", "Sensor8" : "SSLeftINV",
                                        "Sensor9" : "SSLeftDF", "Sensor10" : "SSLeftEVR"})

            if any(e in participantID for e in ["P001", "P002", "P003"]):
                SS = SS.rename(columns={"SSRightEVR" : "SSRightPF", "SSRightDF" : "SSRightINV",
                                        "SSRightINV" : "SSRightDF", "SSRightPF" : "SSRightEVR"})

            if "P015" in participantID:
                SS = SS.rename(columns={"SSRightEVR" : "SSRightINV", "SSRightINV" : "SSRightEVR"})

            # Now use lookup table to find corresponding MoCap file
            # Also pull ID # from SS Filename
            splitFileHandle = SSFilename.split('\\')
            path = "/".join(splitFileHandle[:-1]).replace('StretchSense', 'Motion Capture')
            fn = splitFileHandle[-1].split('-')
            #trialName = trialLookupTable[trialLookupTable['StretchSenseName'] == fn[-1]]
            trialName = trialLookupTable.loc[trialLookupTable['StretchSenseName'] == fn[-1], 'MoCapName']
            MCFilename = path + "/" + fn[0] + "_" + trialName.iloc[0]
            mcColNames = ['Frame #', 'L Foot Inversion', 'L Ankle Flexion', \
                                     'R Foot Inversion', 'R Ankle Flexion']
            MC = pd.read_csv(MCFilename, sep="\t", skiprows=9, names=mcColNames, \
                             usecols=list(range(len(mcColNames))))
            
            # Convert frames to milliseconds based on frame rate of 200Hz
            MC[['Time']] = MC[['Frame #']] / moCapHz

            if "R Foot Inverrsion" in MC.columns:
                MC = MC.rename(columns={"R Foot Inverrsion" : 'R Foot Inversion'})
            
            print("Processing: %s; %s" % (SSFilename.split('/')[-1], MCFilename.split('/')[-1]))

            SSRightPF = proc_utils.approximateStretchSense(SS, "SSRightPF", moCapHz)
            SSRightINV = proc_utils.approximateStretchSense(SS, "SSRightINV", moCapHz)
            SSRightDF = proc_utils.approximateStretchSense(SS, "SSRightDF", moCapHz)
            SSRightEVR = proc_utils.approximateStretchSense(SS, "SSRightEVR", moCapHz)

            # Combine the preprocessed StretchSense data
            framesToMerge = [SSRightPF, SSRightINV, SSRightDF, SSRightEVR]
            rightFoot = reduce(lambda left,right: pd.merge(left,right, how='left', on='Time'),\
                            framesToMerge)

            SSLeftPF = proc_utils.approximateStretchSense(SS, "SSLeftPF", moCapHz)
            SSLeftINV = proc_utils.approximateStretchSense(SS, "SSLeftINV", moCapHz)
            SSLeftDF = proc_utils.approximateStretchSense(SS, "SSLeftDF", moCapHz)
            SSLeftEVR = proc_utils.approximateStretchSense(SS, "SSLeftEVR", moCapHz)

            # Combine the preprocessed StretchSense data
            framesToMerge = [SSLeftPF, SSLeftINV, SSLeftDF, SSLeftEVR]
            leftFoot = reduce(lambda left,right: pd.merge(left,right, how='left', on='Time'),\
                            framesToMerge)

            SS = rightFoot.merge(leftFoot, on='Time', how='left')

            # Line up feet separately
            leftSS = SS[['Time', 'SSLeftPF', 'SSLeftINV', 'SSLeftDF', 'SSLeftEVR']].copy()
            rightSS = SS[['Time', 'SSRightPF', 'SSRightINV', 'SSRightDF', 'SSRightEVR']].copy()

            leftDataNew = proc_utils.adjustForDelayAndCombineMultipleSensor(leftSS, MC, \
                                                                            sensorNameLookUpTable)
            leftMCAndSS = leftDataNew[0][['Time', 'L Foot Inversion', 'L Ankle Flexion', \
                                    'SSLeftPF', 'SSLeftINV', 'SSLeftDF', 'SSLeftEVR']].copy()
            delayTable = delayTable.append({'Trial': MCFilename.split('/')[-1], \
                                            'Foot': "Left", \
                                            'Delay': leftDataNew[1]}, ignore_index=True)

            rightDataNew = proc_utils.adjustForDelayAndCombineMultipleSensor(rightSS, MC, \
                                                                            sensorNameLookUpTable)
            rightMCAndSS = rightDataNew[0][['Time', 'R Foot Inversion', 'R Ankle Flexion', \
                                    'SSRightPF', 'SSRightINV', 'SSRightDF', 'SSRightEVR']].copy()
            delayTable = delayTable.append({'Trial': MCFilename.split('/')[-1], \
                                            'Foot': "Right", \
                                            'Delay': rightDataNew[1]}, ignore_index=True)

            # Remove extra data to make bind_cols cooperate
            rowDiff = len(leftMCAndSS) - len(rightMCAndSS)
            if rowDiff > 0:
                # SSData is longer and needs less rows
                leftMCAndSS = leftMCAndSS[0:-rowDiff]
            elif rowDiff < 0:
                rightMCAndSS = rightMCAndSS[0:rowDiff]
            # If row_diff is 0, then no adjustments needed
            MCAndSS = pd.concat([leftMCAndSS, rightMCAndSS.drop('Time',1)], axis=1)

            tidyMCAndSS = MCAndSS[['Time', 'L Foot Inversion', 'L Ankle Flexion', \
                                   'R Foot Inversion', 'R Ankle Flexion', \
                                   'SSLeftPF', 'SSLeftINV', 'SSLeftDF', 'SSLeftEVR', \
                                   'SSRightPF', 'SSRightINV', 'SSRightDF', 'SSRightEVR']].copy()
            
            # Write to individual files for left and right foot since they 
            # don't always have the same starting point
            leftFn = participantsPath + participantID + "/Preprocessed Data/" + \
                    MCFilename.split('/')[-1].split('.')[0].split('_',1)[-1] + \
                    "_Preprocessed_Left_Foot.csv"
            leftMCAndSS.to_csv(leftFn, index=False)

            rightFn = participantsPath + participantID + "/Preprocessed Data/" + \
                    MCFilename.split('/')[-1].split('.')[0].split('_',1)[-1] + \
                    "_Preprocessed_Right_Foot.csv"
            rightMCAndSS.to_csv(rightFn, index=False)

            # This portion generates plots for visual deubgging of each sensor dataset
            if saveOutput == True:
                print('Plotting Preprocessed Graph... ' + MCFilename.split('/')[-1])
                for rt in sensorNameLookUpTable.itertuples():
                    SSToPlot = rt.SS
                    MCToPlot = rt.MC

                    if ("PF" in SSToPlot) or ("EVR" in SSToPlot):
                        scaledFields = {'SS': scale(tidyMCAndSS[SSToPlot]),
                                        'MC': -scale(tidyMCAndSS[MCToPlot])}
                    else: 
                        scaledFields = {'SS': scale(tidyMCAndSS[SSToPlot]),
                                        'MC': scale(tidyMCAndSS[MCToPlot])}
                    preprocessedData = tidyMCAndSS.assign(**scaledFields)
                    preprocessedData = pd.melt(preprocessedData, id_vars=['Time'], \
                        value_vars=['MC', 'SS'], var_name='Measurement', \
                        value_name='Value')
                    fig, ax = plt.subplots()
                    fig.set_size_inches(6, 4)
                    sns.lineplot(x='Time', y='Value', hue='Measurement', \
                        data=preprocessedData, ax=ax, palette=['#F8766D','#00BFC4'], linewidth=1)
                    box = ax.get_position()
                    ax.set_title("Scaled illustration of lined up data for %s SRS" % SSToPlot[2:])
                    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
                    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

                    preprocessedGaphFn = participantsPath + participantID + \
                        "/Preprocessed Graphs/" + \
                        SSFilename.split('\\')[-1].split('.')[0].split('-')[-1] + \
                        SSToPlot + ".png"
                    fig.savefig(preprocessedGaphFn, dpi=400, bbox_inches="tight")
                    plt.close('all')
    delayTable.to_csv('./delayTable.csv')


if __name__ == "__main__":
    main()