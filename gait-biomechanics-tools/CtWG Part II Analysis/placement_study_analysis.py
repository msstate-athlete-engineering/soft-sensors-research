#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""Postprocessing and analysis of data collected from the placement study

"""
from functools import reduce

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import preprocessing_utils as proc_utils
import os


def main():
    """Placement study analysis script.
    
    This script performs the main processing and visualization of data collected in the
    placement study. 
    """

    # This path must be updated to the directory that contains your participant folders
    participantsPath = os.getcwd() + "/../motionanalyzr/Sample Datasets/SRS Placement " + \
                                     "and Orientation Study/"
    participantsFolders = os.listdir(participantsPath)

    # Adjust this based on the sampling rate of the motion capture system
    moCapHz = 100.0

    # Table that will contain all results of linear models for all trials
    resultsTable = pd.DataFrame(columns=['ID', 'POC', 'Movement', 'AdjRsquared', 'RMSE'])

    # Set this variable to TRUE if you want the preprocessed data and visual
    # output saved to your local filesystem
    saveOutput = True
    
    # Iterate thorugh each participant folder, gather data and analyze it
    for participantID in participantsFolders:
        participantFiles = os.listdir(participantsPath + participantID)
        # Get lists of filenames based on their file extension Gather StretchSense Files
        SSFiles = [filename for filename in participantFiles if filename.endswith(".csv")]

        # Create directories to hold reformatted data outputs
        preprocessedGraphDir = participantsPath + participantID + "/Preprocessed Graphs"
        if not os.path.exists(preprocessedGraphDir):
            os.mkdir(preprocessedGraphDir)

        preprocessedDataDir = participantsPath + participantID + "/Preprocessed Data"
        if not os.path.exists(preprocessedDataDir):
            os.mkdir(preprocessedDataDir)

        residualGraphDir = participantsPath + participantID + "/Residual Graphs"
        if not os.path.exists(residualGraphDir):
            os.mkdir(residualGraphDir)

        # Iterate through each trial based on file names
        for _, SSFilename in enumerate(SSFiles):
            print("Formatting... ", SSFilename)
            # We are parsing the files based on the way that StretchSense data is reported from
            # their proprietary iOS Bluetooth application Columns are named manually based on
            # where each soft robotic sensor (SRS) SRS was positioned during the experiment
            ssColNames = ['Seq', 'Sample', 'Time', 'DF', 'EVR', 'PF', 'INV']
            stretchSenseData = pd.read_csv(participantsPath + participantID + '/' + SSFilename, \
                                            names=ssColNames, skiprows=1, \
                                            usecols=list(range(len(ssColNames))))

            # Inversion and eversion sensors were mounted backwards for this particular participant
            if "P301" in SSFilename:
                stretchSenseData = stretchSenseData.rename(columns={'INV' : 'EVR', 'EVR' : 'INV'})

            # Because the naming convention for the MoCap and StretchSense files are the same,
            # it can be assumed that they will have the same file index in their respective list

            MCFilename = SSFilename.replace('-','_').replace('.csv','.exp')
            moCapData = pd.read_csv(participantsPath + participantID + '/' + MCFilename, \
                                    sep="\t", skiprows=7, usecols=list(range(3)))
            # Convert frames to milliseconds based on frame rate of 100Hz
            moCapData[['Time']] = moCapData[['Frame #']] / moCapHz

            # Update frequency of StrechSense samples to match Motion capture samples.
            # Since SRS data was collected at roughly 25 Hz, but samples were not recorded
            # at consistent intervals, the approximate function was used to predict SRS values
            # as if the data was collected at a stable rate that matches the motion capture rate
            DF = proc_utils.approximateStretchSense(stretchSenseData, "DF", moCapHz)
            PF = proc_utils.approximateStretchSense(stretchSenseData, "PF", moCapHz)

            INV = proc_utils.approximateStretchSense(stretchSenseData, "INV", moCapHz)
            EVR = proc_utils.approximateStretchSense(stretchSenseData, "EVR", moCapHz)

            # Combine the preprocessed StretchSense data
            framesToMerge = [DF, PF, INV, EVR]
            SSMatched = reduce(lambda left,right: pd.merge(left,right, how='left', on='Time'),\
                               framesToMerge)

            # Preprocess and model data based on file name (i.e. What movement are we analyzing?)
            # The following operation extracts the movement from the file name
            footMovement = MCFilename.split('_')[-1].split('.')[0]

            # Small fix for correcting legacy naming convention
            if footMovement == "IN":
                footMovement = "INV"
            elif footMovement == "EV":
                footMovement = "EVR"

            # Since motion capture reports these values in the negative plane, we want to note
            # in our modeling that this results in an inverse relationship between
            # sensor stretch and joint angle
            if footMovement == "PF" or footMovement == "EVR":
                invertMoCap = True
            else:
                invertMoCap = False

            # Note which planar movement we are comparing our stretch sensor data to
            # Variable is assigned based on how planar movements were labelled in
            # MotionMonitor software
            # Ankle Plantarflexion = Sagittal Plane
            # Ankle Inversion      = Frontal Plane
            if footMovement == "DF" or footMovement == "PF":
                planarMovement = "Ankle Plantarflexion"
            else:
                planarMovement = "Ankle Inversion"

            # Adjust for timing delay between MoCap and StretchSense
            # Foot movementa and planar movement identified to determine what
            # data we will use to find the delay
            # We will invert the MoCap data if we are measuring plantar flexion or eversion
            combinedDatasets = proc_utils.adjustForDelayAndCombine(SSMatched, moCapData, \
                                                footMovement, planarMovement, invertMoCap)
            combinedDatasets = proc_utils.removeDataBelowStartingAngle(combinedDatasets, \
                                                                       planarMovement)
            combinedDatasets.reset_index(inplace=True, drop=True)
            
            # Perform linear regression then evaluate model performance with RMSE and R^2 metrics
            stretchSenseLinearModel = LinearRegression().fit(combinedDatasets[[footMovement]],\
                                                  combinedDatasets[[planarMovement]])

            predictedDataset = stretchSenseLinearModel.predict(combinedDatasets[[footMovement]])
            modelVerification = pd.DataFrame({'Actual' : combinedDatasets[planarMovement],\
                                         'Predicted' : np.array(predictedDataset).flatten()}, \
                                         columns= ['Actual','Predicted'])
            root_mean_squared_error = round(np.sqrt(mean_squared_error(\
                                             modelVerification[['Actual']],\
                                             modelVerification[['Predicted']])), 4)
            adjR_2 = round(r2_score(modelVerification[['Actual']],\
                                    modelVerification[['Predicted']]), 4)

            plotTitle = "Aligned, Scaled Preview of " + footMovement + " (SRS) vs.\n" \
                        + planarMovement + " (MoCap),\nTrial: " + SSFilename
            preprocessedGraph = proc_utils.plotPreprocessedScaled(combinedDatasets, \
                                                        planarMovement, footMovement, plotTitle)

            plotTitle = "Residuals: " + MCFilename[0:-4]
            residualGraph = proc_utils.plotResiduals(combinedDatasets, stretchSenseLinearModel, \
                                                     planarMovement, footMovement, adjR_2, \
                                                     root_mean_squared_error, plotTitle)

            # Add adjusted R-squared value to table
            pID = SSFilename[0:4]
            position = SSFilename[5:7]

            resultsTable = resultsTable.append({'ID' : pID,\
                                 'POC' : position,\
                                 'Movement' : footMovement,\
                                 'AdjRsquared' : adjR_2,\
                                 'RMSE' : root_mean_squared_error}, ignore_index=True)

            # Uncomment this block to produce images of lined up data and residual graphs.
            # Also save .csv file of lined up data. Comment out this block if you don't want
            # to save and just want to work with the table.


            if saveOutput == True:
                print('Plotting Preprocessed Graph... ' + MCFilename)

                preprocessedGraphFn = participantID + '/Preprocessed Graphs/' + \
                                 SSFilename.split('.')[0] + '_Aligned_Scaled.png'
                preprocessedFig = preprocessedGraph.get_figure()
                preprocessedFig.savefig(participantsPath + preprocessedGraphFn, \
                                        dpi=400, bbox_inches="tight")

                print('Saving Preprocessed Data... ' + MCFilename)

                preprocessedDataFn = participantID + '/Preprocessed Data/' + \
                                 SSFilename.split('.')[0] + '_Preprocessed.csv'
                combinedDatasets.to_csv(participantsPath + preprocessedDataFn)

                print('Plotting Residual Visualization... ' + MCFilename)

                residualGraphFn = participantID + '/Residual Graphs/' + \
                                 SSFilename.split('.')[0] + '_Residuals.png'
                residualFig = residualGraph.get_figure()
                residualFig.savefig(participantsPath + residualGraphFn, \
                                    dpi=400, bbox_inches="tight")

            plt.close('all')

    # Rename position values to POC
    resultsTable[['POC']] = resultsTable[['POC']].replace("P1", "POC1")
    resultsTable[['POC']] = resultsTable[['POC']].replace("P2", "POC2")
    resultsTable[['POC']] = resultsTable[['POC']].replace("P3", "POC3")

    # Remove bad trials
    resultsTable = resultsTable[resultsTable['AdjRsquared'] >= 0.6]

    resultsTable.append({'ID' : pID,\
                         'POC' : position,\
                         'Movement' : footMovement,\
                         'AdjRsquared' : adjR_2,\
                         'RMSE' : root_mean_squared_error}, ignore_index=True)

    # Add rows for missing/bad trials based on average of previous data
    # Trials to replace:
    # P304_P1_IN, P306_P1_DF, P309_P3_EV
    avg_P1_INV = resultsTable[(resultsTable['POC'] == 'POC1') & \
                              (resultsTable['Movement'] == "INV")]
    avg_R2 = avg_P1_INV['AdjRsquared'].agg(np.mean)
    avg_rmse = avg_P1_INV['RMSE'].agg(np.mean)

    resultsTable.append({'ID' : "P304",\
                         'POC' : "POC1",\
                         'Movement' : "INV",\
                         'AdjRsquared' : avg_R2,\
                         'RMSE' : avg_rmse}, ignore_index=True)

    # P306_P1_DF
    avg_P1_DF = resultsTable[(resultsTable['POC'] == 'POC1') & \
                             (resultsTable['Movement'] == "DF")]
    avg_R2 = avg_P1_DF['AdjRsquared'].agg(np.mean)
    avg_rmse = avg_P1_DF['RMSE'].agg(np.mean)

    resultsTable.append({'ID' : "P304",\
                         'POC' : "POC1",\
                         'Movement' : "DF",\
                         'AdjRsquared' : avg_R2,\
                         'RMSE' : avg_rmse}, ignore_index=True)

    # P309_P3_EV
    avg_P3_EVR = resultsTable[(resultsTable['POC'] == 'POC3') & \
                              (resultsTable['Movement'] == "EVR")]
    avg_R2 = avg_P3_EVR['AdjRsquared'].agg(np.mean)
    avg_rmse = avg_P3_EVR['RMSE'].agg(np.mean)

    resultsTable.append({'ID' : "P304",\
                         'POC' : "POC1",\
                         'Movement' : "DF",\
                         'AdjRsquared' : avg_R2,\
                         'RMSE' : avg_rmse}, ignore_index=True)

    POCMaxes = resultsTable.groupby(['Movement', 'POC'], as_index=False).mean()
    POCMaxes = POCMaxes.sort_values(['AdjRsquared'], ascending=False)
    POCMaxes = POCMaxes.sort_values(['Movement'], ascending=True)
    POCMaxes = POCMaxes.drop_duplicates(subset='Movement', keep='first').reset_index(drop=True)
    del POCMaxes['RMSE']
    print("POC Maxes for AdjRsquared:")
    print(POCMaxes)

    POCMins = resultsTable.groupby(['Movement', 'POC'], as_index=False).mean()
    POCMins = POCMins.sort_values(['RMSE'], ascending=True)
    POCMins = POCMins.sort_values(['Movement'], ascending=True)
    POCMins = POCMins.drop_duplicates(subset='Movement', keep='first').reset_index(drop=True)
    del POCMins['AdjRsquared']
    print("POC Mins for RMSE:")
    print(POCMins)

    finalResults = resultsTable.groupby(['Movement', 'POC']).agg({
        "AdjRsquared" : [np.mean, np.std], \
        "RMSE" : [np.mean, np.std]})

    print(finalResults)


if __name__ == "__main__":
    main()
