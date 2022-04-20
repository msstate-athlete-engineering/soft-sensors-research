% Training an LSTM 

function [ trainPerformance,testPerformance, trainrmse, testrmse ] = LSTM_Net (Input,Target,Inds,trial)

    
     trainrmse= cell(1,size (Inds,1)); % cell array for saving the RMSE values for train set
     testrmse= cell(1,size (Inds,1)); % cell array for saving the RMSE values for test set
     
     trainPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over various folds for train set.
     testPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over various folds for test set.
     
     
     
for i = 1:size (Inds,1) % iterate through participants
    Indcs= Inds{i}; % get the train- test gait cycle IDs for all the folds
    

   
    for j=1:size(Indcs,1) % iterate through folds
        traininput= Input(Indcs{j,1}); % get the inputs (SRS data) for the trianing data
        testinput=Input(Indcs{j,2});  % get the inputs (SRS data) for the test data
        traintarget= Target(Indcs{j,1}); % get the outputs (MoCap data) for the trianing data
        testtarget= Target(Indcs{j,2}); % get the outputs (MoCap data) for the test data

        
        
        
 % % setting the LSTM network parameters     
        
numFeatures = 4; % number of features in input (sequesnce) layer: 4 columns from 4 mounted SRS sensors
numHiddenUnits1 = 125; % number of hidden units in the first LSTM layer
numHiddenUnits2 = 100; % number of hidden units in the second LSTM layer

numResponses = 1; % number of outputs to be predicted

% defining the network architecture
layers = [ ...
    sequenceInputLayer(numFeatures)  % sequence layer for feding input data to the model 
   lstmLayer(numHiddenUnits1,'OutputMode','sequence') % first LSTM layer 
    dropoutLayer(0.5) % drop out layer to randomly (50%) sets input elements to zero to avoid over fitting
   lstmLayer(numHiddenUnits2,'OutputMode','sequence') % second LSTM layer 
    dropoutLayer(0.5) % drop out layer to randomly (50%) sets input elements to zero to avoid over fitting
    fullyConnectedLayer(numResponses) % fully connected layer to combine all the features to predict the output of model
    regressionLayer]; % calculating the error loss of predictions
 
% setting the training options
options = trainingOptions('adam', ...  
    'MaxEpochs',1500, ...
    'GradientThreshold',1, ...
    'Verbose',0, ... 
    'Plots','training-progress');

% training the network
[net,info] = trainNetwork(traininput,traintarget,layers,options);

% getting the model predictions for the test set
YPred = predict(net,testinput);

errorstest=cell(3,1); % empty cell for the prediction errors for each test set including 3 gaits
err=0;
el=0;
for k=1:3  %iterate through gaits in the test set
errorstest{k} = gsubtract(testtarget{k},YPred{k}); % get the prediction errors for each gait 
err=err+sum(errorstest{k}.^2);  % add the summation of the squared-errors for each gait to get the total error values for the test set
el=el+numel(errorstest{k}); % add the total number of samples in each gait to get the total number of samples in the test set

end

% calculate and storing the RMSE values
MSE= err/el;
trainrmse {i}(1,j) = info.TrainingRMSE(end); 
testrmse {i}(1,j)= sqrt(MSE);

% save the LSTM network
%{
name1=trial+"_net_P_"+i+"_CV_"+j;
 name2=trial+"_info_P_"+i+"_CV_"+j;
 % save (name1, 'net')
 % save (name2, 'info')

%}
clear net
clear info
    end

     trainPerformance(i)= mean(trainrmse {i}); % claculate the average error over folds for the training set
     testPerformance(i)= mean(testrmse {i}); % claculate the average error over folds for the test set
   %  save("tr",'trainPerformance')
   %  save("te",'testPerformance')
delete(findall(0));
%save("trRMSE",'trainrmse')
%save("teRMSE",'testrmse')
end
%save()
end

