%% Introduction

%{
MATLAB scripts for "Closing the Wearable Gap—Part VI: Human Gait Recognition Using Deep Learning Methodologies"

In this paper the capacitance of soft robotic sensors (SRS) related to foot-ankle basic movements
was quantified during the gait movements of 20 participants on a flat surface as well as a cross-sloped
surface (inclined). The SRS data is compared against a 3D motion capture (MoCap) system to
illustrate the performance of SRS in analyzing joint angles.

Three different approaches were employed to quantify the relationship between the SRS and the MoCap system,
including multivariable linear regression, an artificial neural network (ANN), and a time-series long
short-term memory (LSTM) network. Models were compared based on the root mean squared error
(RMSE) of the prediction of the joint angle of the foot in the sagittal and frontal plane, collected from
the MoCap system.

Each participant completed two different experiments while wearing a pair of socks with the SRS placed over bony landmarks,
walking on a flat surface and walking on a inclined surface with a 10 degrees slope.
Each participant walked six times across each walkway, generating 12 trials in total. During each trial,
participants completed two to three complete gait cycles based on their stride length.


In this paper, eight different models for each participant have been developed (using each modeling approach) to
model the relationship among four categories of data (left foot(L), right foot (R), flat surface(F), inclined surface(I)).
For each model, four sets of inputs (DF, PF, INV, and EVR SRS) are used to
predict two sets of output data (Flexion:F, Inversion:I). 
There are 4 combinations of input data (Surface-Foot(SF) combination) and 2 combination of output data. 
Therefore, a total of 8 combination of input-output data exists and 8 models are developed for each participant.
The 4 SF combination and 8 input-output pairs of data are as follows:

FL:Flat surface-Left foot
FLF: Flat surface-Left foot-Flexion output of MoCap
FLV: Flat surface-Left foot-Inversion output of MoCap

FR:Flat surface-Right foot
FRF: Flat surface-Right foot-Flexion output of MoCap
FRV: Flat surface-Right foot-Inversion output of MoCap

IL:Inclined surface-Left foot
ILF: Inclined surface-Left foot-Flexion output of MoCap
ILV: Inclined surface-Left foot-Inversion output of MoCap

IR:Inclined surface-Right foot
IRF: Inclined surface-Right foot-Flexion output of MoCap
IRV: Inclined surface-Right foot-Inversion output of MoCap


%}


%% Load Data
    % Data from each gait cycle has been stored into an CSV file and the
    % name of each CSV file reflects the participant number, trial name,
    % foot, and gait number.
     [Data, mainFolder, CSV_filepaths] = Load_data ();
     % Data: a cell array containing all gait cycles , mainFolder: Folder containing the excel files, CSV_filepaths: file paths for all excell files
   


%% Rearranging data
 % Adding 4 columns to data indicating the participant number, trial name, foot, and gait number                         
 
    [DataL,SF]= Arranging(Data,mainFolder, CSV_filepaths); 
    % DaataL a cell array containing all gait cycles. Each cell has an matrix with 11 columns:
    %1 column time stamp, 2 columns MoCap data (Flextion/Inversion), 4 columns SRS data
    % 4 columns data labels (participant number, trial name, foot, and gait number)

    % SF an array indicating each cell of DataL is corresponding to which
    % Surface-Foot combination.
    
%% Separating trials

% creating separate matrices for surface-foot combinations and their input,
% flexion output, inversion output, labels, and timestamp.
         

[FR_inputs, FRF_targets, FRV_targets,FR_labels, FR_time]      = Separate_trials (DataL, SF, "FR");



[FL_inputs, FLF_targets, FLV_targets,FL_labels, FL_time]      = Separate_trials (DataL, SF, "FL");



[IR_inputs, IRF_targets, IRV_targets,IR_labels, IR_time]      = Separate_trials (DataL, SF, "IR");



[IL_inputs, ILF_targets, ILV_targets,IL_labels, IL_time]      = Separate_trials (DataL, SF, "IL");

  
%% Train-validation-test spliting (ANN & Regression)

% Creating a cell array indicationg indices for train data, validation data and test data.  
% Participants completed 6 trials, 3-fold cross validation has been carried out for train-test spliting. 
% 4 trials has been selected as the training set and 2 trials has been considered as the test set (one trial test set and one trial validation set for ANN)  
% This has been repeated 3 times so that all the trials have been set as the test/validation set once. 

[FR_Inds]=splitting_train_test (FR_labels);       
[FL_Inds]=splitting_train_test (FL_labels);       
[IR_Inds]=splitting_train_test (IR_labels);       
[IL_Inds]=splitting_train_test (IL_labels); 

% XX_Inds are the cell array containing the mask for each train-validation-test set for each participant.


%% ANN

% A few network architectures have been tested including architectures with one or two hidden layers. 
% The best network with the lowest error has been selected for each participant.  

hiddenLayer={10,5,10,[1,5],[1,10],[2,10],[5,10]};% the number of neurons in the hidden layer(s), 

%FR

%FRF

% Creating empty cells for saving RMSE values of models. XXX_trainRMSE has
% size(hiddenLayer,2) rows for saving the results from various network
% architectures and size(FR_Inds,1) columns for saving the RMSE results for
% Each participant. Each cell of XXX_trainRMSE has RMSE results for various
% train-val-test split (n-folds).

FRF_trainRMSE=cell(size(hiddenLayer,2),size(FR_Inds,1));
FRF_testRMSR=cell(size(hiddenLayer,2),size(FR_Inds,1));
FRF_valRMSE=cell(size(hiddenLayer,2),size(FR_Inds,1));


% Creating an empty array for saving the average RMSE values over n-fold.
FRF_trainPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1));
FRF_testPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1));
FRF_valPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1));


for s=1:size(hiddenLayer,2) % Iterate through various network architechures. 
    
    hiddenLayerSize=hiddenLayer{s};
    [ FRF_trainPerformance(s,:),FRF_testPerformance(s,:), FRF_valPerformance(s,:),...
        FRF_trainRMSE(s,:), FRF_testRMSR(s,:), FRF_valRMSE(s,:) ] = ANN_Net (FR_inputs,FRF_targets,hiddenLayerSize,FR_Inds,"FRF");
end

% Selecting the best architecture for each participant and getting the minimum errors
FRF_trainPerformance_ANN=min(FRF_trainPerformance);
FRF_testPerformance_ANN=min(FRF_testPerformance);
FRF_valPerformance_ANN=min(FRF_valPerformance);


%FRV

FRV_trainPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1)); 
FRV_testPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1));
FRV_valPerformance=zeros(size(hiddenLayer,2),size(FR_Inds,1));
FRV_trainRMSE=cell(size(hiddenLayer,2),size(FR_Inds,1));
FRV_testRMSR=cell(size(hiddenLayer,2),size(FR_Inds,1));
FRV_valRMSE=cell(size(hiddenLayer,2),size(FR_Inds,1));

for s=1:size(hiddenLayer,2) % running the ANN for each architechure. 
    hiddenLayerSize=hiddenLayer{s};
    [ FRV_trainPerformance(s,:),FRV_testPerformance(s,:), FRV_valPerformance(s,:),...
        FRV_trainRMSE(s,:), FRV_testRMSR(s,:) , FRV_valRMSE(s,:)] = ANN_Net (FR_inputs,FRV_targets,hiddenLayerSize,FR_Inds,"FRV");
end
% Selecting the best architecture for each participant and getting the minimum errors
FRV_trainPerformance_ANN=min(FRV_trainPerformance);
FRV_testPerformance_ANN=min(FRV_testPerformance);
FRV_valPerformance_ANN=min(FRV_valPerformance);


%FL

%FLF

FLF_trainPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLF_testPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLF_valPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLF_trainRMSE=cell(size(hiddenLayer,2),size(FL_Inds,1));
FLF_testRMSR=cell(size(hiddenLayer,2),size(FL_Inds,1));
FLF_valRMSE=cell(size(hiddenLayer,2),size(FL_Inds,1));

for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
hiddenLayerSize=hiddenLayer{s};
[ FLF_trainPerformance(s,:),FLF_testPerformance(s,:),FLF_valPerformance(s,:),...
    FLF_trainRMSE(s,:), FLF_testRMSR(s,:) , FLF_valRMSE(s,:) ] = ANN_Net (FL_inputs,FLF_targets,hiddenLayerSize,FL_Inds,"FLF");
end

% Selecting the best architecture for each participant and getting the minimum errors
FLF_trainPerformance_ANN=min(FLF_trainPerformance);
FLF_testPerformance_ANN=min(FLF_testPerformance);
FLF_valPerformance_ANN=min(FLF_valPerformance);

%FLV

FLV_trainPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLV_testPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLV_valPerformance=zeros(size(hiddenLayer,2),size(FL_Inds,1));
FLV_trainRMSE=cell(size(hiddenLayer,2),size(FL_Inds,1));
FLV_testRMSR=cell(size(hiddenLayer,2),size(FL_Inds,1));
FLV_valRMSE=cell(size(hiddenLayer,2),size(FL_Inds,1));

for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
    hiddenLayerSize=hiddenLayer{s};
    [ FLV_trainPerformance(s,:),FLV_testPerformance(s,:),FLV_valPerformance(s,:),...
        FLV_trainRMSE(s,:), FLV_testRMSR(s,:) , FLV_valRMSE(s,:)] = ANN_Net (FL_inputs,FLV_targets,hiddenLayerSize,FL_Inds,"FLV");
end

% Selecting the best architecture for each participant and getting the minimum errors
FLV_trainPerformance_ANN=min(FLV_trainPerformance);
FLV_testPerformance_ANN=min(FLV_testPerformance);
FLV_valPerformance_ANN=min(FLV_valPerformance);




%IR

%IRFtrial="IRF";

IRF_trainPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRF_testPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRF_valPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRF_trainRMSE=cell(size(hiddenLayer,2),size(IR_Inds,1));
IRF_testRMSR=cell(size(hiddenLayer,2),size(IR_Inds,1));
IRF_valRMSE=cell(size(hiddenLayer,2),size(IR_Inds,1));


for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
    hiddenLayerSize=hiddenLayer{s};
    [ IRF_trainPerformance(s,:),IRF_testPerformance(s,:), IRF_valPerformance(s,:),...
        IRF_trainRMSE(s,:), IRF_testRMSR(s,:), IRF_valRMSE(s,:) ] = ANN_Net (IR_inputs,IRF_targets,hiddenLayerSize,IR_Inds,"IRF");
end

% Selecting the best architecture for each participant and getting the minimum errors
IRF_trainPerformance_ANN=min(IRF_trainPerformance);
IRF_testPerformance_ANN=min(IRF_testPerformance);
IRF_valPerformance_ANN=min(IRF_valPerformance);


%IRVtrial="IRV";

IRV_trainPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRV_testPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRV_valPerformance=zeros(size(hiddenLayer,2),size(IR_Inds,1));
IRV_trainRMSE=cell(size(hiddenLayer,2),size(IR_Inds,1));
IRV_testRMSR=cell(size(hiddenLayer,2),size(IR_Inds,1));
IRV_valRMSE=cell(size(hiddenLayer,2),size(IR_Inds,1));

for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
    hiddenLayerSize=hiddenLayer{s};
    [ IRV_trainPerformance(s,:),IRV_testPerformance(s,:), IRV_valPerformance(s,:),...
        IRV_trainRMSE(s,:), IRV_testRMSR(s,:) , IRV_valRMSE(s,:)] = ANN_Net (IR_inputs,IRV_targets,hiddenLayerSize,IR_Inds,"IRV");
end

% Selecting the best architecture for each participant and getting the minimum errors
IRV_trainPerformance_ANN=min(IRV_trainPerformance);
IRV_testPerformance_ANN=min(IRV_testPerformance);
IRV_valPerformance_ANN=min(IRV_valPerformance);


%IL

%ILFtrial="ILF";

ILF_trainPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILF_testPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILF_valPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILF_trainRMSE=cell(size(hiddenLayer,2),size(IL_Inds,1));
ILF_testRMSR=cell(size(hiddenLayer,2),size(IL_Inds,1));
ILF_valRMSE=cell(size(hiddenLayer,2),size(IL_Inds,1));

for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
    hiddenLayerSize=hiddenLayer{s};
    [ ILF_trainPerformance(s,:),ILF_testPerformance(s,:),ILF_valPerformance(s,:),...
        ILF_trainRMSE(s,:), ILF_testRMSR(s,:) , ILF_valRMSE(s,:) ] = ANN_Net (IL_inputs,ILF_targets,hiddenLayerSize,IL_Inds,"ILF");
end

% Selecting the best architecture for each participant and getting the minimum errors
ILF_trainPerformance_ANN=min(ILF_trainPerformance);
ILF_testPerformance_ANN=min(ILF_testPerformance);
ILF_valPerformance_ANN=min(ILF_valPerformance);

%ILVtrial="ILV";

ILV_trainPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILV_testPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILV_valPerformance=zeros(size(hiddenLayer,2),size(IL_Inds,1));
ILV_trainRMSE=cell(size(hiddenLayer,2),size(IL_Inds,1));
ILV_testRMSR=cell(size(hiddenLayer,2),size(IL_Inds,1));
ILV_valRMSE=cell(size(hiddenLayer,2),size(IL_Inds,1));

for s=1:size(hiddenLayer,2)% running the ANN for each architechure. 
hiddenLayerSize=hiddenLayer{s};
[ ILV_trainPerformance(s,:),ILV_testPerformance(s,:),ILV_valPerformance(s,:),...
    ILV_trainRMSE(s,:), ILV_testRMSR(s,:) , ILV_valRMSE(s,:)] = ANN_Net (IL_inputs,ILV_targets,hiddenLayerSize,IL_Inds,"ILV");
end

% Selecting the best architecture for each participant and getting the minimum errors
ILV_trainPerformance_ANN=min(ILV_trainPerformance);
ILV_testPerformance_ANN=min(ILV_testPerformance);
ILV_valPerformance_ANN=min(ILV_valPerformance);


% Aggregate ANN results

ANN_result= vertcat(FRF_trainPerformance_ANN, FRF_testPerformance_ANN ,FRV_trainPerformance_ANN ,...
    FRV_testPerformance_ANN,FLF_trainPerformance_ANN, FLF_testPerformance_ANN, FLV_trainPerformance_ANN, FLV_testPerformance_ANN, ...
    IRF_trainPerformance_ANN,IRF_testPerformance_ANN,IRV_trainPerformance_ANN,IRV_testPerformance_ANN,ILF_trainPerformance_ANN,...
    ILF_testPerformance_ANN, ILV_trainPerformance_ANN, ILV_testPerformance_ANN);

ANN_result_train= vertcat(FRF_trainPerformance_ANN ,FRV_trainPerformance_ANN,FLF_trainPerformance_ANN ,FLV_trainPerformance_ANN,...
    IRF_trainPerformance_ANN,IRV_trainPerformance_ANN, ILF_trainPerformance_ANN, ILV_trainPerformance_ANN);

ANN_AvgResult_train= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), mean(ANN_result_train,2));

ANN_SDResult_train= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), std(ANN_result_train,0,2));

ANN_result_test= vertcat(FRF_testPerformance_ANN , FRV_testPerformance_ANN,FLF_testPerformance_ANN, FLV_testPerformance_ANN,...
    IRF_testPerformance_ANN,IRV_testPerformance_ANN,ILF_testPerformance_ANN,ILV_testPerformance_ANN);

ANN_AvgResult_test= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), mean(ANN_result_test,2));

ANN_SDResult_test= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), std(ANN_result_test,0,2));

%%  Linear modeling

% FR

% "FRF";
[ FRF_trainPerformance_Linear, FRF_testPerformance_Linear, ...
    FRF_trainRMSE_Linear, FRF_testRMSR_Linear ] = LinearModeling (FR_inputs,FRF_targets,FR_Inds);


% "FRV";
[ FRV_trainPerformance_Linear,FRV_testPerformance_Linear, ...
    FRV_trainRMSE_Linear, FRV_testRMSR_Linear ] = LinearModeling (FR_inputs,FRV_targets,FR_Inds);


% FL
    
% "FLF";

[ FLF_trainPerformance_Linear,FLF_testPerformance_Linear, ...
    FLF_trainRMSE_Linear, FLF_testRMSR_Linear ] = LinearModeling (FL_inputs,FLF_targets,FL_Inds);


% "FLV";
[ FLV_trainPerformance_Linear,FLV_testPerformance_Linear, ...
    FLV_trainRMSE_Linear, FLV_testRMSR_Linear ] = LinearModeling (FL_inputs,FLV_targets,FL_Inds);


% IR

% "IRF";
[ IRF_trainPerformance_Linear,IRF_testPerformance_Linear, ...
    IRF_trainRMSE_Linear, IRF_testRMSR_Linear ] = LinearModeling (IR_inputs,IRF_targets,IR_Inds);


% "IRV";
[ IRV_trainPerformance_Linear,IRV_testPerformance_Linear, ...
    IRV_trainRMSE_Linear, IRV_testRMSR_Linear ] = LinearModeling (IR_inputs,IRV_targets,IR_Inds);



% IL

% "ILF";
[ILF_trainPerformance_Linear,ILF_testPerformance_Linear, ...
    ILF_trainRMSE_Linear, ILF_testRMSR_Linear ] = LinearModeling (IL_inputs,ILF_targets,IL_Inds);


% "ILV";
[ILV_trainPerformance_Linear,ILV_testPerformance_Linear, ...
    ILV_trainRMSE_Linear, ILV_testRMSR_Linear ] = LinearModeling (IL_inputs,ILV_targets,IL_Inds);


% Aggregate regression results

Linear_result= vertcat(FRF_trainPerformance_Linear, FRF_testPerformance_Linear ,FRV_trainPerformance_Linear ,...
    FRV_testPerformance_Linear,FLF_trainPerformance_Linear, FLF_testPerformance_Linear, FLV_trainPerformance_Linear,...
    FLV_testPerformance_Linear, IRF_trainPerformance_Linear,IRF_testPerformance_Linear,IRV_trainPerformance_Linear,...
    IRV_testPerformance_Linear,ILF_trainPerformance_Linear, ILF_testPerformance_Linear, ILV_trainPerformance_Linear, ILV_testPerformance_Linear);

Linear_result_train= vertcat(FRF_trainPerformance_Linear ,FRV_trainPerformance_Linear,FLF_trainPerformance_Linear, FLV_trainPerformance_Linear,...
    IRF_trainPerformance_Linear,IRV_trainPerformance_Linear, ILF_trainPerformance_Linear, ILV_trainPerformance_Linear);


Linear_AvgResult_train= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), mean(Linear_result_train,2));

Linear_SDResult_train= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), std(Linear_result_train,0,2));


Linear_result_test= vertcat(FRF_testPerformance_Linear , FRV_testPerformance_Linear,FLF_testPerformance_Linear, FLV_testPerformance_Linear,...
    IRF_testPerformance_Linear,IRV_testPerformance_Linear,ILF_testPerformance_Linear,ILV_testPerformance_Linear);

Linear_AvgResult_test= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), mean(Linear_result_test,2));

Linear_SDResult_test= horzcat(vertcat("FRF" ,"FRV","FLF" ,"FLV",...
    "IRF","IRV", "ILF", "ILV"), std(Linear_result_test,0,2));



%% LSTM


% LSTM is sensitive to the length of the sequence and is not
% capable of handling the data in the form of long sequences like a complete trial. Therefore, gait cycles
% are considered as individual sequences of data for training and testing LSTM.

% creating separate matrices for surface-foot combinations and their input,
% flexion output, inversion output, labels, and timestamp.


% "FR"
[LSTM_FR_inputs, LSTM_FRF_targets, LSTM_FRV_targets,LSTM_FR_labels, LSTM_FR_time]      = LSTM_Separate_trials (DataL, SF, "FR");

% "FL"
[LSTM_FL_inputs, LSTM_FLF_targets, LSTM_FLV_targets,LSTM_FL_labels, LSTM_FL_time]      = LSTM_Separate_trials (DataL, SF, "FL");

% "IR"
[LSTM_IR_inputs, LSTM_IRF_targets, LSTM_IRV_targets,LSTM_IR_labels, LSTM_IR_time]      = LSTM_Separate_trials (DataL, SF, "IR");

% "IL"
[LSTM_IL_inputs, LSTM_ILF_targets, LSTM_ILV_targets,LSTM_IL_labels, LSTM_IL_time]      = LSTM_Separate_trials (DataL, SF, "IL");



% % Spliting train - test sets

% creating a cell array indicationg train data, and test data.  
% Participants completed 12-18 gait cycles, 3 gaits have been considered as the test data and the remaining gaits as training data.
% This process is repeated so that all the gaits appear in the test set,
% therefore, depending on the number of gaits, it might be 4-fold CV,
% 5-fold CV, or 6-fold CV.


[LSTM_FR_Inds]=LSTM_train_test_split (LSTM_FR_labels);       
[LSTM_FL_Inds]=LSTM_train_test_split (LSTM_FL_labels);       
[LSTM_IR_Inds]=LSTM_train_test_split (LSTM_IR_labels);       
[LSTM_IL_Inds]=LSTM_train_test_split (LSTM_IL_labels);       


% % training and testing the LSTM network using the data

% FR

% "FRF"

[ FRF_trainPerformance_LSTM,FRF_testPerformance_LSTM,...
    FRF_trainRMSE_LSTM, FRF_testRMSR_LSTM ] = LSTM_Net (LSTM_FR_inputs,LSTM_FRF_targets,LSTM_FR_Inds,"FRF");

% "FRV"
[ FRV_trainPerformance_LSTM,FRV_testPerformance_LSTM,...
    FRV_trainRMSE_LSTM, FRV_testRMSR_LSTM ] = LSTM_Net (LSTM_FR_inputs,LSTM_FRV_targets,LSTM_FR_Inds,"FRV");

% "FLF"

[ FLF_trainPerformance_LSTM,FLF_testPerformance_LSTM,...
    FLF_trainRMSE_LSTM, FLF_testRMSR_LSTM ] = LSTM_Net (LSTM_FL_inputs,LSTM_FLF_targets,LSTM_FL_Inds,"FLF");


% "FLV"
[ FLV_trainPerformance_LSTM,FLV_testPerformance_LSTM,...
    FLV_trainRMSE_LSTM, FLV_testRMSR_LSTM ] = LSTM_Net (LSTM_FL_inputs,LSTM_FLV_targets,LSTM_FL_Inds,"FLV");



% "IRF"
[ IRF_trainPerformance_LSTM,IRF_testPerformance_LSTM,...
    IRF_trainRMSE_LSTM, IRF_testRMSR_LSTM ] = LSTM_Net (LSTM_IR_inputs,LSTM_IRF_targets,LSTM_IR_Inds,"IRF");


% "IRV"
[IRV_trainPerformance_LSTM,IRV_testPerformance_LSTM,...
    IRV_trainRMSE_LSTM, IRV_testRMSR_LSTM ] = LSTM_Net (LSTM_IR_inputs,LSTM_IRV_targets,LSTM_IR_Inds,"IRV");
  

%"ILF"
[ILF_trainPerformance_LSTM,ILF_testPerformance_LSTM,...
    ILF_trainRMSE_LSTM, ILF_testRMSR_LSTM ] = LSTM_Net (LSTM_IL_inputs,LSTM_ILF_targets,LSTM_IL_Inds,"ILF");


% "ILV"
[ILV_trainPerformance_LSTM,ILV_testPerformance_LSTM,...
    ILV_trainRMSE_LSTM, ILV_testRMSR_LSTM ] = LSTM_Net (LSTM_IL_inputs,LSTM_ILV_targets,LSTM_IL_Inds,"ILV");


% Aggregate LSTM results

LSTM_result= vertcat(FRF_trainPerformance_LSTM, FRF_testPerformance_LSTM ,FRV_trainPerformance_LSTM , FRV_testPerformance_LSTM,FLF_trainPerformance_LSTM,...
    FLF_testPerformance_LSTM, FLV_trainPerformance_LSTM, FLV_testPerformance_LSTM, ...
    IRF_trainPerformance_LSTM,IRF_testPerformance_LSTM,IRV_trainPerformance_LSTM,...
    IRV_testPerformance_LSTM,ILF_trainPerformance_LSTM, ILF_testPerformance_LSTM, ILV_trainPerformance_LSTM, ILV_testPerformance_LSTM);

LSTM_result_train= vertcat(FRF_trainPerformance_LSTM ,FRV_trainPerformance_LSTM,FLF_trainPerformance_LSTM ,FLV_trainPerformance_LSTM...
    ,IRF_trainPerformance_LSTM,IRV_trainPerformance_LSTM, ILF_trainPerformance_LSTM, ILV_trainPerformance_LSTM);

LSTM_result_test= vertcat(FRF_testPerformance_LSTM , FRV_testPerformance_LSTM,FLF_testPerformance_LSTM, FLV_testPerformance_LSTM,...
    IRF_testPerformance_LSTM,IRV_testPerformance_LSTM,ILF_testPerformance_LSTM,ILV_testPerformance_LSTM);

%% Violin plots

% drawing violin plots for RMSE values across various surfaces, foot, 
% methods (Linear regression, ANN, and LSTM), and MoCap outputs (Flexion
% and Inversion)

% RMSE results are saved in a cell array (4,3) called "results", and each cell again is a cell array(1,2) for
% keeping RMSE results from the right and left foot. 
% Each row in the "results" array is related to an specific walking surface Surface and specific output of MoCap. 
% The results from various modeling methods are in 3 columns.

% 4*3 subplots have been created. subplots in each row are corresponding to
% the cells of the "results" array and there are 2 violin plots in each
% subplot for data from left and right foot.


results=cell(4,3);
results {1,1}={FLF_testPerformance_Linear,FRF_testPerformance_Linear};
results {1,2}={FLF_testPerformance_ANN,FRF_testPerformance_ANN};
results {1,3}={FLF_testPerformance_LSTM,FRF_testPerformance_LSTM};

results {2,1}={FLV_testPerformance_Linear,FRV_testPerformance_Linear};
results {2,2}={FLV_testPerformance_ANN,FRV_testPerformance_ANN};
results {2,3}={FLV_testPerformance_LSTM,FRV_testPerformance_LSTM};

results {3,1}={ILF_testPerformance_Linear,IRF_testPerformance_Linear};
results {3,2}={ILF_testPerformance_ANN,IRF_testPerformance_ANN};
results {3,3}={ILF_testPerformance_LSTM,IRF_testPerformance_LSTM};

results {4,1}={ILV_testPerformance_Linear,IRV_testPerformance_Linear};
results {4,2}={ILV_testPerformance_ANN,IRV_testPerformance_ANN};
results {4,3}={ILV_testPerformance_LSTM,IRV_testPerformance_LSTM};


clf
grid on
space=1.1;
alpha=0.88;
sd=10;
%mtd=["Linear Regression", "ANN", "LSTM"];


for i=1:3 % Iterate through various methods Linear Regression
for j=1:4
  
ah(1)=subplot(4,3,(j-1)*3+i); 

data_l=results{j,i}{1}'; % getting data for the left foot
data_r=results{j,i}{2}'; % getting data for the right foot


% calculating IQR for the left foot
n=numel(data_l); % number of participants
[y_l,x_l]=hist(data_l);
y_l=smooth(y_l,sd)';
y_l=y_l./max(y_l);
dataR=tiedrank (data_l)./n;
IQR_l=data_l([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% calculating IQR for the right foot
[y_r,x_r]=hist(data_r);
y_r=smooth(y_r,sd)';
y_r=y_r./max(y_r);
dataR=tiedrank (data_r)./n;
IQR_r=data_r([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% plotting the violin plots for the left and right foot and their corresponding mean, median, and IQR 
grid on
hold on
% subtracting or adding space in the following lines are just inserting distance between violin plot for the left and right foot
obj1=patch ([y_l-space -space-y_l(end:-1:1)], [x_l x_l(end:-1:1)], "g", "facealpha", .5); 
obj2=patch ([y_r+space  space-y_r(end:-1:1)], [x_r x_r(end:-1:1)], "b", "facealpha", .5);
obj3=plot ([-space -space], IQR_l, "k", "linew", 3);
obj4=plot (-space, mean (data_l),"ks", "markerfacecolor", "r", "markersize",10);
obj5=plot (-space, median (data_l),"ko", "markerfacecolor", "g", "markersize",10);


set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
plot ([space space], IQR_r, "k", "linew", 3)
plot (space, mean (data_r),"ks", "markerfacecolor", "r", "markersize",10)
plot (space, median (data_r),"ko", "markerfacecolor", "g", "markersize",10)

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
hold off


if j==1  % inserting the title just for the first subplot in each column 
    if i==1
        title ({"Linear Regression"," "},'fontweight','bold','fontsize',24)
    elseif i==2
        title ({"ANN"," "},'fontweight','bold','fontsize',24)
    else
        title ({"LSTM"," "},'fontweight','bold','fontsize',24)
    end
end


set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])

hold off
if i==1 % inserting the y-ticks just for the first subplot in each row (the most left subplot)
    if j==1
        ylabel({"Flexion" , "Flat Surface"," "}  ,'fontweight','bold','fontsize',18)
    elseif j==2
        ylabel({"Inversion" , "Flat Surface"," "} ,'fontweight','bold','fontsize',18)
    elseif j==3    
        ylabel({"Flexion" , "Slopped Surface"," "}  ,'fontweight','bold','fontsize',18)
    elseif j==4
        ylabel( {"Inversion" , "Slopped Surface"," "} ,'fontweight','bold','fontsize',18)
    end

% Setting the legends
hL = legend([obj1,obj2],{'  Left Foot  ','  Right Foot  '} ,'fontweight','bold','fontsize',18,'Orientation','vertical');
newPosition = [0.86 0.6 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
if i==2
hL = legend([obj3,obj4,obj5],{ "  IQR  ", "  Mean  " , "  Median  "} ,'fontweight','bold','fontsize',18);
newPosition = [0.85 0.3 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
end


end



%% Violin Plots for Sloped surface- Flexion output of MoCap- right foot excluding data from participant 4


clf
grid on
space=0;
alpha=0.88;
sd=10;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Sloped surface- Flexion output of MoCap- right foot %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

for i=1:3 % Iterate through various methods Linear Regression, ANN, and LSTM
for j=3
  
ah(1)=subplot(1,3,i); 


data_r=results{j,i}{2}'; % getting data for the right foot


data_r(4)=[]; % excluding data from participant 4



% calculating IQR for the right foot
n=numel(data_l); % number of participants
[y_r,x_r]=hist(data_r);
y_r=smooth(y_r,sd)';
y_r=y_r./max(y_r);
dataR=tiedrank (data_r)./n;
IQR_r=data_r([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% plotting the violin plots for the right foot and its corresponding mean, median, and IQR 
grid on
hold on
% subtracting or adding space in the following lines are just inserting distance between violin plot for the left and right foot

obj2=patch ([y_r+space  space-y_r(end:-1:1)], [x_r x_r(end:-1:1)], "b", "facealpha", .5);

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
obj3=plot ([space space], IQR_r, "k", "linew", 3);
obj4=plot (space, mean (data_r),"ks", "markerfacecolor", "r", "markersize",10);
obj5=plot (space, median (data_r),"ko", "markerfacecolor", "g", "markersize",10);

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
hold off


    if i==1
        title ({"Linear Regression"," "},'fontweight','bold','fontsize',24)
        ylabel({"Inversion" , "Slopped Surface"," "},  'fontweight','bold','fontsize',20)  % inserting the label for y-axis just for the first subplot in each row (the most left subplot)
    elseif i==2
        title ({"ANN"," "},'fontweight','bold','fontsize',24)
    else
        title ({"LSTM"," "},'fontweight','bold','fontsize',24)
    end

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])

hold off
if i==1 % inserting the y-ticks just for the first subplot in each row (the most left subplot)
   
        ylabel({"Flexion" , "Slopped Surface"," "}  ,'fontweight','bold','fontsize',18)
        % Setting the legends  
end
end
if i==2
hL = legend([obj3,obj4,obj5],{ "  IQR  ", "  Mean  " , "  Median  "} ,'fontweight','bold','fontsize',18);
newPosition = [0.85 0.4 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
end

%% plot row data

    
    
p=17; % selecting the participant
Indcs= IR_Inds{p};  %Get the indices for various trials of an specific Surface-Foot combination
data= IR_inputs;  %Get the indices for various trials of an specific Surface-Foot combination
tit={"Participant "+p, "Right Foot - Sloped Surface"}  ; % set the title of plot


    figure()
    for j=1:size(Indcs,1)% Iterate through each participant's indices 
        for k=1:2
            subplot (3,2,2*(j-1)+k)
            for p=1:4 % Iterate through 4 SRS and ploting them
                s1=plot (1:size(data(:,Indcs{j,k+1}),2),data(1,Indcs{j,k+1}));
                hold on
                s2=plot (1:size(data(:,Indcs{j,k+1}),2),data(2,Indcs{j,k+1}));
                s3=plot (1:size(data(:,Indcs{j,k+1}),2),data(3,Indcs{j,k+1}));
                s4=plot (1:size(data(:,Indcs{j,k+1}),2),data(4,Indcs{j,k+1}));
                hold off 
            end
            
            % setting title for subtitles
            t=2*(j-1)+k;
            title( "Trial "+ t,'fontweight','bold','fontsize',22)
   
        end
    end
    %setting legend 
    hL = legend([s1,s2,s3,s4],{"DF", "PF", "INV", "EVR"} ,'fontweight','bold','fontsize',18); %,'Orientation', 'horizontal'
    newPosition = [0.85 0.4 0.2 0.2];
    newUnits = 'normalized';
    set(hL,'Position', newPosition,'Units', newUnits);
    
    % setting the super title
    sup=suptitle(tit);


