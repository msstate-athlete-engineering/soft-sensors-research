#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""Utility functions to help with preprocessing of StretchSense and Motion Capture data.

    A collection of helper functions to be used in various analysis scripts.
"""

from typing import List
import matplotlib
from matplotlib.colors import LinearSegmentedColormap

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import interpolate, signal
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import scale

plt.style.use('ggplot')
plt.rcParams["axes.labelsize"] = 10
plt.rcParams["axes.titlesize"] = 14

cmap = LinearSegmentedColormap.from_list(
    name='test', 
    colors=['blue','red']
)

def approximateStretchSense(SSData: pd.DataFrame, sensor: str, moCapHz: int) -> pd.DataFrame:
    """Interpolate StretchSense values to desired rate.
    
    Takes the data from StretchSense and interpolates it based on the sampling rate of 
    the MoCap system.
    
    Args:
        SSData (pd.DataFrame): Stretch Sensor data
        sensor (str): Identifier for which sensor to process
        moCapHz (int): frequency of Motion Capture
    
    Returns:
        approximatedMovement (pd.DataFrame): Interpolated Stretch Sensor data
    """
    
    if str != type(sensor):
        raise TypeError("Sensor parameter must be string!")

    # Determine time stamps using indexing and MoCap Recording Rate
    newInput = np.arange(start = SSData["Time"].iloc[0],\
                           stop = SSData["Time"].iloc[-1],\
                           step = (1 / moCapHz))

    approximateSensorValue = interpolate.interp1d(list(SSData["Time"].values),\
                                                  list(SSData[sensor].values),\
                                                  fill_value='extrapolate')

    data = {'Time': newInput, sensor: approximateSensorValue(newInput)}
    approximatedMovement = pd.DataFrame(data, columns = ['Time', sensor])

    return approximatedMovement

def adjustForDelayAndCombine(SSData: pd.DataFrame, MCData: pd.DataFrame,\
                             SSMovementName: str, MCMovementName: str,\
                             invert: bool = False) -> pd.DataFrame:
    """Adjust time delay between datasets for single sensor.
    
    Adjusts time delay between datasets using cross correlation, puts both datasets in
    one table, and filters out any data points where the Motion Capture was less 
    than its starting point.

    Args:
        SSData (pd.DataFrame): Stretch Sensor data
        MCData (pd.DataFrame): Motion Capture data
        SSMovementName (str): Name of the Stretch Sensor Movement
        MCMovementName (str): Name of the Motion Capture Movement
        invert (bool): Whether to invert the Motion Capture data

    Returns:
        moCapAndSS (pd.DataFrame): The combined Motion Capture and Stretch Sensor datasets
    """
    
    # Line up data using cross correlation. Basically, slide one dataset across
    # the other until you get the optimal r-squared value
    if True == invert:
        MCData[[MCMovementName]] = -MCData[[MCMovementName]]
    
    delay = ccf(SSData[SSMovementName], MCData[MCMovementName])

    # Remove values that aren't needed and "slide" dataset back to zero milliseconds
    if delay >= 0:
        SSData = SSData.drop(list(range(delay)))
        del SSData['Time']
        SSData.reset_index(inplace=True, drop=True)
    else:
        MCData = MCData.drop(list(range(-delay)))
        del MCData['Time']
        MCData.reset_index(inplace=True, drop=True)
    
    # Remove extra data to make bind_cols cooperate
    rowDiff = len(SSData) - len(MCData)
    if rowDiff > 0:
        # SSData is longer and needs less rows
        SSData = SSData[0:-rowDiff]
    elif rowDiff < 0:
        MCData = MCData[0:rowDiff]

    # Combine datasets
    moCapAndSS = pd.concat([SSData, MCData], axis=1)

    return moCapAndSS

def adjustForDelayAndCombineMultipleSensor(SSData: pd.DataFrame, MCData: pd.DataFrame,\
                                           sensorLookupTable: pd.DataFrame) -> pd.DataFrame:
    """Adjust time delay between datasets for multiple sensors.

    Adjusts time delay between datasets using cross correlation, puts both datasets in one
    table, and filters out any data points where the Motion Capture was less
    than its starting point

    Args: 
        SSData (pd.DataFrame): Stretch Sensor data
        MCData (pd.DataFrame): Motion Capture data
        sensorLookupTable (pd.DataFrame): Table which specifies sensor number to location

    Returns:
        moCapAndSS (pd.DataFrame): The combined Motion Capture and Stretch Sensor datasets
    """
    bestACF = 0

    if "Right" in SSData.columns[1]:
        dataNames = sensorLookupTable.iloc[[0,2]]
    elif "Left" in SSData.columns[1]:
        dataNames = sensorLookupTable.iloc[[4,6]]
    else:
        raise IOError("SSData column name contained neither Left or Right!")

    # "Pre-screen" to see which movement is best for lining up data
    for row in range(len(dataNames)):
        MCMovement = dataNames.iloc[row, 0]
        SSMovement = dataNames.iloc[row, 1]

        if ("PF" in SSMovement) or ("EVR" in  SSMovement):
            delay = ccf(SSData[SSMovement], -MCData[MCMovement])
        else:
            delay = ccf(SSData[SSMovement], MCData[MCMovement])

        movementACF = abs(delay)
        if movementACF > bestACF:
            MCToAdjust = MCMovement
            SSToAdjust = SSMovement
            bestDelay = delay

    print("Best matching movement: %s" % SSToAdjust)

    # Now line up data based on best resulting sensor
    delay = bestDelay
    print("Delay to adjust: %d" % delay)

    # Remove values that aren't needed and "slide" dataset back to zero milliseconds
    if delay >= 0:
        SSData = SSData.drop(list(range(delay)))
        del SSData['Time']
        SSData.reset_index(inplace=True, drop=True)
    else:
        MCData = MCData.drop(list(range(-delay)))
        del MCData['Time']
        MCData.reset_index(inplace=True, drop=True)
    
    # Remove extra data to make bind_cols cooperate
    rowDiff = len(SSData) - len(MCData)
    if rowDiff > 0:
        # SSData is longer and needs less rows
        SSData = SSData[0:-rowDiff]
    elif rowDiff < 0:
        MCData = MCData[0:rowDiff]

    # Combine datasets
    moCapAndSS = pd.concat([SSData, MCData], axis=1)

    return [moCapAndSS, delay]
    
def removeDataBelowStartingAngle(combinedData: pd.DataFrame, MCMovement: str) -> pd.DataFrame:
    """Drop Data that occured before starting angle.

    Alter the combined Motion Capture and Stretch Sensor dataset to exclude data before
    starting angle of interest.

    Args:
        combinedData (pd.DataFrame): Combined Motion Capture and Stretch Sensor dataset
        MCMovement (str): Name of the Motion Capture movement

    Returns:
        adjustedData (pd.DataFrame): Adjusted dataset according to starting angle
    """
    return combinedData[combinedData[MCMovement] >= combinedData[MCMovement].iloc[0]]

def plotPreprocessedScaled(combinedData: pd.DataFrame, MCMovement: str, \
                           SSMovement: str, plotTitle: str) -> matplotlib.axes.SubplotBase:
    """Plot preprocessed data of combined dataset.

    Using the combined Motion Capture and Stretch Sensor dataset, plot dataset for a
    specified Motion Capture and Stretch Sensor movement prior to any postprocessing.

    Args:
        combinedData (pd.DataFrame): Combined Motion Capture and Stretch Sensor dataset
        MCMovement (str): Name of the Motion Capture movement
        SSMovement (str): Name of the Stretch Sensor movement
        plotTitle (matplotlib.axes.SubplotBase): Title of the plot

    Returns:
        preprocessedScaledPlot (plt): Plot of preprocessed data
    """
    scaled_fields = {'Motion Capture': scale(combinedData[MCMovement]),
                     'SRS': scale(combinedData[SSMovement])}
    preprocessed_data = combinedData.assign(**scaled_fields)
    preprocessed_data = pd.melt(preprocessed_data, id_vars=['Time'], \
        value_vars=['Motion Capture', 'SRS'], var_name='Measurement Method', \
        value_name='Scaled Value')
    
    fig, ax = plt.subplots()
    fig.set_size_inches(6, 4)
    preprocessedScaledPlot = sns.scatterplot(x='Time', y='Scaled Value', \
        hue='Measurement Method', data=preprocessed_data, palette=['#F8766D','#00BFC4'], \
        ax=ax, edgecolors='none', linewidth=0)
    box = ax.get_position()
    ax.set_title(plotTitle)
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

    return preprocessedScaledPlot

def plotResiduals(combinedData: pd.DataFrame, model: LinearRegression, \
                MCMovement: str, SSMovement: str, R2: float, RMSE: float, \
                plotTitle: str) -> matplotlib.axes.SubplotBase:
    """Plot residuals of combined dataset for a given model.

    Using the combined Motion Capture and Stretch Sensor dataset, plot residuals for a
    specified Motion Capture and Stretch Sensor movement according to the passed model.

    Args:
        combinedData (pd.DataFrame): Combined Motion Capture and Stretch Sensor dataset
        model (LinearRegression): Model that defines relationships between measurements
                                  and biomechanical movement
        MCMovement (str): Name of the Motion Capture movement
        SSMovement (str): Name of the Stretch Sensor movement
        R2 (float): R-squared score of model
        RMSE (float): root-mean-square-error score of model
        plotTitle (str): Title of the plot

    Returns:
        residualPlot (matplotlib.axes.SubplotBase): Plot of postprocessed data
    """
    combinedData['MCPredicted'] = model.predict(combinedData[[SSMovement]])
    combinedData['Residuals'] = abs(combinedData[MCMovement] - combinedData['MCPredicted'])

    subTitle = "Angle = " + str(round(model.intercept_[0],2)) + " + " + \
               str(round(model.coef_[0][0],2)) + "pF, Adj. R-squared = " + \
               str(R2) + ", RMSE = " + str(RMSE)

    fig, ax = plt.subplots()
    fig.set_size_inches(6, 4)

    points = plt.scatter(combinedData[SSMovement], combinedData[MCMovement],
                        c=combinedData['Residuals'], s=10, cmap=cmap)
    clb = plt.colorbar(points, shrink=0.5, aspect=5)
    clb.ax.set_title('abs(residuals)', loc='left', fontdict={'fontsize': 9})

    residualPlot = sns.scatterplot(x=SSMovement, y=MCMovement, hue='Residuals', size='Residuals', \
                                   sizes=(20,160), palette=cmap, data=combinedData, ax=ax, \
                                   legend=False, edgecolor='none', linewidth=0, zorder=3)
    
    residualPlot = sns.scatterplot(x=SSMovement, y='MCPredicted', data=combinedData, size = 8, \
                                   palette='clear', ax=ax, legend=False, edgecolor='k', \
                                   facecolors='none', linewidth=0.3, zorder=2)
    
    ax.plot([combinedData[SSMovement].min(), combinedData[SSMovement].max()], \
            [combinedData['MCPredicted'].min(), combinedData['MCPredicted'].max()], \
            color='#808080', linewidth=1.5, zorder=0)
    
    for _, r in combinedData.iterrows():
        ymin=min(r['MCPredicted'], r[MCMovement])
        ymax=max(r['MCPredicted'], r[MCMovement])
        plt.vlines(r[SSMovement], ymin=ymin, ymax=ymax, color='#A9A9A9', linewidth=0.5, zorder=1)
    
    plt.suptitle(plotTitle,fontsize=14, x=0.31, y=0.98)
    plt.title(subTitle,fontsize=9, loc='left')

    xlabel = ax.xaxis.get_label().get_text()
    ax.set_xlabel(xlabel + " (StretchSense: Capacitance in pF)")

    ylabel = ax.yaxis.get_label().get_text()
    ax.set_ylabel(ylabel + " (MoCap: Angle in Degrees)")

    return residualPlot

def ccf(x : pd.Series, y : pd.Series) -> int:
    """Performs cross correlation on passed data.

    Helper function which produces the same output as R's ccf() function.

    Args:
        x, y (pd.Series): Numeric vector or time series
    
    Returns:
        lag (int): lag index between input vectors
    """
    x = x.to_numpy()
    y = y.to_numpy()

    arr_length = min(len(x),len(y))
    x = x[:arr_length]
    y = y[:arr_length]

    x = (x - np.mean(x))
    y = (y - np.mean(y))

    result = np.correlate(y, x, mode='full') / (np.std(x) * np.std(y) * arr_length)
    lag = (len(x) - 1) - result.argmax()
    return lag
