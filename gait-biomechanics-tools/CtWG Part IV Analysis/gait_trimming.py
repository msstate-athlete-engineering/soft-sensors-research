#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""Trimming gait data to specified length.

"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
import glob

plt.style.use('ggplot')
plt.rcParams["axes.labelsize"] = 10
plt.rcParams["axes.titlesize"] = 14


def main():
    """Gait study trimming script.
    
    Script to clip up preprocessed data based on timestamps collected from
    motion capture playback.

    """

    saveOutput = False

    delayTable = pd.read_csv('./delayTable.csv')

    # Load up files from dataset
    # This path must be updated to the directory that contains your participant folders
    participantsPath = os.getcwd() + "/../motionanalyzr/Sample Datasets/SRS Gait Study/"
    participantsFolders = os.listdir(participantsPath)

    for participantID in participantsFolders:
            # Create directories to hold reformatted data outputs
            gaitCyclesDir = participantsPath + participantID + "/Gait Cycles/"
            if not os.path.exists(gaitCyclesDir):
                os.mkdir(gaitCyclesDir)
            files = glob.glob(gaitCyclesDir + "*")
            for fn in files:
                os.remove(fn)

            gaitCycleImagesDir = participantsPath + participantID + "/Gait Cycle Images/"
            if not os.path.exists(gaitCycleImagesDir):
                os.mkdir(gaitCycleImagesDir)

    # Trim files based on timestamps collected from MotionMonitor
    gaitFrames = pd.read_excel('./GaitFrameData.xlsx')

    # Iterate through each row of data to gather points at which to trim up the
    # .csv file. These points represent the right foot heel strike which
    # we are considering as the beginning of the gait cycle
    for gaitData in gaitFrames.itertuples():
        # Look up file
        trialName = gaitData.Participant + '_' + gaitData.Trial + '.exp'
        
        tidyDataPath = participantsPath + gaitData.Participant + '/Preprocessed Data/'

        leftFootData = pd.read_csv(tidyDataPath + gaitData.Trial + '_Preprocessed_Left_Foot.csv')
        leftDelay = delayTable[(delayTable['Trial'] == trialName) & \
                            (delayTable['Foot'] == "Left")]['Delay'].iloc[0]
        rightFootData = pd.read_csv(tidyDataPath + gaitData.Trial + '_Preprocessed_Right_Foot.csv')
        rightDelay = delayTable[(delayTable['Trial'] == trialName) & \
                            (delayTable['Foot'] == "Right")]['Delay'].iloc[0]
        gaitCyclePath = participantsPath + gaitData.Participant + '/Gait Cycles/'

        # Iterate through the timestamp columns which are used to identify beginning
        # of each gait cycle
        gaitCycleNumber = 1
        # Columns 8-11 of gaitData represent our timestamp columns
        # We don't include column 11 in our iteration since that is just used to mark
        # the end of the last gait cycles
        for idx in range(3,7):
            # Frame number = row number - 1
            timeStampStart = gaitData[idx] - 1
            # Gait cycle ends at the timestamp immediately before the next gait
            # cycle begins
            timeStampEnd = (gaitData[idx + 1] - 1) - 1

            # The following statement checks if either timestamp is NaN.
            # In python, NaN == NaN evaluates to False
            if timeStampStart == timeStampStart and timeStampEnd == timeStampEnd:

                # If delay is negative, then beginning of motion capture was trimmed
                # To resolve this, the timestamps need to be adjusted to account for
                # the delay that was trimmed out of the dataset
                if leftDelay < 0:
                    timeStampStart = timeStampStart + leftDelay
                    timeStampEnd = timeStampEnd + leftDelay

                timeStampStart = int(timeStampStart)
                timeStampEnd = int(timeStampEnd)

                leftGaitCycle = leftFootData[timeStampStart:timeStampEnd + 1]

                # Reset timestamp to original first. The reason we do these separate
                # is that the two stretchsense modules (each foot) were not always in sync with
                # each other
                if rightDelay < 0:
                    timeStampStart = timeStampStart - leftDelay + rightDelay
                    timeStampEnd = timeStampEnd - leftDelay + rightDelay

                timeStampStart = int(timeStampStart)
                timeStampEnd = int(timeStampEnd)

                rightGaitCycle = rightFootData[timeStampStart:timeStampEnd + 1]

                # Write to new .csv file for each foot for each gait cycle
                leftGaitCycle.to_csv(gaitCyclePath + gaitData.Trial + \
                                    '_LF_Gait_' + str(gaitCycleNumber) + '.csv', index=False)
                rightGaitCycle.to_csv(gaitCyclePath + gaitData.Trial + \
                                    '_RF_Gait_' + str(gaitCycleNumber) + '.csv', index=False)

                gaitCycleNumber = gaitCycleNumber + 1

    if saveOutput == True:
        for participantID in participantsFolders:
            gaitFiles = glob.glob(participantsPath + participantID +'/Gait Cycles/*.csv')
            for gaitFn in gaitFiles:
                gaitCycleData = pd.read_csv(gaitFn)
                
                fig, ax = plt.subplots(nrows=2,ncols=1)
                fig.set_size_inches(6, 5)
                ssColumns = gaitCycleData.columns.to_list()[3:7]
                mcColumns = gaitCycleData.columns.to_list()[1:3]
                ssGaitCycleData = pd.melt(gaitCycleData, id_vars=['Time'], \
                    value_vars=ssColumns, var_name='StretchSense Sensor', \
                    value_name='Capacitance (pF)')
                sns.lineplot(x='Time', y='Capacitance (pF)', \
                    hue='StretchSense Sensor', data=ssGaitCycleData, ax=ax[0], \
                    linewidth=1.5)
                box = ax[0].get_position()
                ax[0].set_title("StretchSense Data for Trial %s" % gaitFn.split('\\')[-1])
                ax[0].set_position([box.x0, box.y0, box.width * 0.8, box.height])
                ax[0].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

                mcGaitCycleData = pd.melt(gaitCycleData, id_vars=['Time'], \
                    value_vars=mcColumns, var_name='MoCap Movement', \
                    value_name='Angle')
                sns.lineplot(x='Time', y='Angle', \
                    hue='MoCap Movement', data=mcGaitCycleData, ax=ax[1], \
                    linewidth=1.5, palette=['#F8766D','#00BFC4'])
                box = ax[1].get_position()
                ax[1].set_title("Motion Capture Data for Trial %s" % gaitFn.split('\\')[-1])
                ax[1].set_position([box.x0, box.y0, box.width * 0.8, box.height])
                ax[1].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

                plt.tight_layout()

                gaitCycleImageFn = participantsPath + participantID +'/Gait Cycle Images/' + \
                    gaitFn.split('\\')[-1].split('.')[0] + '.png'
                fig.savefig(gaitCycleImageFn, dpi=400, bbox_inches="tight")
                plt.close('all')

if __name__ == "__main__":
    main()
