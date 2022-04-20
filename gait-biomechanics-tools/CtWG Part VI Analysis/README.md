MATLAB scripts for "Closing the Wearable Gap—Part VI: Human Gait Recognition Using Deep Learning Methodologies"

# Abstract 
In this paper the capacitance of soft robotic sensors (SRS) related to foot-ankle basic movements was quantified during the gait movements of 20 participants on a flat surface as well as a cross-sloped surface (inclined). The SRS data is compared against a 3D motion capture (MoCap) system to illustrate the performance of SRS in analyzing joint angles.
 
Three different approaches were employed to quantify the relationship between the SRS and the MoCap system, including multivariable linear regression, an artificial neural network (ANN), and a time-series long short-term memory (LSTM) network. Models were compared based on the root mean squared error (RMSE) of the prediction of the joint angle of the foot in the sagittal and frontal plane, collected from the MoCap system.
 
Each participant completed two different experiments while wearing a pair of socks with the SRS placed over bony landmarks, walking on a flat surface and walking on a inclined surface with a 10 degrees slope. Each participant walked six times across each walkway, generating 12 trials in total. During each trial, participants completed two to three complete gait cycles based on their stride length.
 
 
# Input-Output
In this paper, eight different models for each participant have been developed (using each modeling approach) to
model the relationship among four categories of data (left foot(L), right foot (R), flat surface(F), inclined surface(I)).
For each model, four sets of inputs (DF, PF, INV, and EVR SRS) are used to predict two sets of output data (Flexion: F, Inversion: I).  There are 4 combinations of input data (Surface-Foot (SF) combination) and 2 combination of output data. 
Therefore, a total of 8 combination of input-output data exists and 8 models are developed for each participant. The 4 SF combination and 8 input-output pairs of data are as follows:
 
**FL**: Flat Surface-Left Foot<br>
**FLF**: Flat Surface-Left Foot -Flexion output of MoCap<br>
**FLV**: Flat Surface-Left Foot -Inversion output of MoCap<br>
 
**FR**: Flat Surface-Right Foot<br>
**FRF**: Flat Surface-Right Foot -Flexion output of MoCap<br>
**FRV**: Flat Surface-Right Foot -Inversion output of MoCap<br>

**IL**: Inclined Surface-Left Foot<br>
**ILF**: Inclined Surface-Left Foot -Flexion output of MoCap<br>
**ILV**: Inclined Surface-Left Foot -Inversion output of MoCap<br>
 
**IR**: Inclined Surface-Right Foot<br>
**IRF**: Inclined Surface-Right Foot -Flexion output of MoCap<br>
**IRV**: Inclined Surface-Right Foot -Inversion output of MoCap<br>

 
# Implementation
The analysis can be performed by simply running the **Main.m** file. This will execute all of the subsequent data preprocessing, training, modeling, analysis, and evaluation scripts included with the software package. The training for the deep learning algorithms will take anywhere from several hours to a day depending on the system being used and GPU. 
