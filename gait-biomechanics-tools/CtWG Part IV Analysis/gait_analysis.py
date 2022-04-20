#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""Gait study analysis file.

"""

import os
import glob
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


def main():
    """Gait study analysis script.
    
    This script performs the main processing of data collected in the gait study. 
    """
    participantsPath = os.getcwd() + "/../motionanalyzr/Sample Datasets/SRS Gait Study/"
    participantsFolders = os.listdir(participantsPath)

    resultsTable = pd.DataFrame(columns=['Participant', 'Trial', 'Foot', 'Gait Cycle', \
                                        'Movement', 'MAE', 'RMSE', 'AdjRsquared'])

    for participantID in participantsFolders:
        gaitCycleFiles = glob.glob(participantsPath + participantID + '/Gait Cycles/*.csv')
        for gaitCycleFilename in gaitCycleFiles:
            # Keep this if statement to keep from analyzing third gait cycle
            cycleData = pd.read_csv(gaitCycleFilename)
            trialName = gaitCycleFilename.split('\\')[-1][:-4].replace("Gait_", "")

            if "INV" in trialName:
                trialName.replace("_", "")

            # filter to smooth out stretchsense data
            ssColumns = cycleData.columns.to_list()[3:7]
            invCol = cycleData.columns.to_list()[1]
            flexCol = cycleData.columns.to_list()[2]

            cycleData[ssColumns] = cycleData[ssColumns].apply(lambda x : savgol_filter(x, 39, 3))
            SSData = cycleData[ssColumns].sum(axis=1).to_frame()

            invModel = LinearRegression().fit(SSData, cycleData[[invCol]])

            invPredicted = invModel.predict(SSData)
            modelVerification = pd.DataFrame({'Actual' : cycleData[invCol],\
                                         'Predicted' : np.array(invPredicted).flatten()}, \
                                         columns= ['Actual','Predicted'])
            invModel_rmse = round(np.sqrt(mean_squared_error(\
                                             modelVerification[['Actual']],\
                                             modelVerification[['Predicted']])), 4)
            invModel_mae = round(mean_absolute_error(\
                                             modelVerification[['Actual']],\
                                             modelVerification[['Predicted']]), 4)
            invModel_adjR_2 = round(r2_score(modelVerification[['Actual']],\
                                    modelVerification[['Predicted']]), 4)

            flexModel = LinearRegression().fit(SSData, cycleData[[flexCol]])

            flexPredicted = flexModel.predict(SSData)
            modelVerification = pd.DataFrame({'Actual' : cycleData[flexCol],\
                                         'Predicted' : np.array(flexPredicted).flatten()}, \
                                         columns= ['Actual','Predicted'])
            flexModel_rmse = round(np.sqrt(mean_squared_error(\
                                             modelVerification[['Actual']],\
                                             modelVerification[['Predicted']])), 4)
            flexModel_mae = round(mean_absolute_error(\
                                             modelVerification[['Actual']],\
                                             modelVerification[['Predicted']]), 4)
            flexModel_adjR_2 = round(r2_score(modelVerification[['Actual']],\
                                    modelVerification[['Predicted']]), 4)

            if "WALK" in trialName:
                trialType = "Flat Surface (FS)"
            else:
                trialType = "Tilted Surface Platform (TSP)"
            
            foot = trialName[-4:-2]
            gaitCycle = trialName[-1]

            resultsTable = resultsTable.append({'Participant' : participantID,\
                                                'Trial' : trialType,\
                                                'Foot' : foot,\
                                                'Gait Cycle' : gaitCycle,\
                                                'Movement' : "Inversion",\
                                                'RMSE' : invModel_rmse,\
                                                'MAE' : invModel_mae,\
                                                'AdjRsquared' : invModel_adjR_2},\
                                                ignore_index=True)
                                            
            resultsTable = resultsTable.append({'Participant' : participantID,\
                                                'Trial' : trialType,\
                                                'Foot' : foot,\
                                                'Gait Cycle' : gaitCycle,\
                                                'Movement' : "Flexion",\
                                                'RMSE' : flexModel_rmse,\
                                                'MAE' : flexModel_mae,\
                                                'AdjRsquared' : flexModel_adjR_2},\
                                                ignore_index=True)
    resultsTable.to_csv('./GaitResults.csv', index=False)

if __name__ == "__main__":
    main()
