function [ trainPerformance,testPerformance,validationPerformance, trainrmse, testrmse,validationrmse ] = ANN_Net (Input,Target,hiddenLayerSize,Inds,trial)

     trainrmse= cell(1,size (Inds,1)); % cell array for saving the RMSE values for train set
     validationrmse= cell(1,size (Inds,1)); % cell array for saving the RMSE values for validation set
     testrmse= cell(1,size (Inds,1)); % cell array for saving the RMSE values for test set
     
     trainPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over 3-fold for train set.
     validationPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over 3-fold for validation set.
     testPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over 3-fold for test set.
   
     
 
     
for i = 1:size (Inds,1) % iterating over the participants
    Indcs= Inds{i};
    
    for j=1:size(Indcs,1) % iterating over n-folds
        traininput= Input(:,Indcs{j,1}); % getting the inputs (SRS data) for the train set trials
        validationinput= Input(:,Indcs{j,2}); % getting the inputs (SRS data) for the validation set trials
        testinput= Input(:,Indcs{j,3}); % getting the inputs (SRS data) for the test set trials
    
        traintarget= Target(Indcs{j,1});  % getting the outputs (Mocap data) for the train set trials
        validationtarget= Target(Indcs{j,2});  % getting the inputs (Mocap data) for the validation set trials
        testtarget= Target(Indcs{j,3});  % getting the inputs (Mocap data) for the test set trials
        



net = fitnet(hiddenLayerSize); % set up the architecture of the network

net.divideFcn = 'divideind'; % determin the policy for deviding train-val-test sets 
trainInd=find(Indcs{j,1}==1); % getting the train set IDs
valInd=find(Indcs{j,2}==1); % getting the validation set IDs
testInd=find(Indcs{j,3}==1); % getting the test set IDs
newInput=horzcat(Input(:,trainInd),Input(:,valInd),Input(:,testInd)); % concatenating Input values (SRS data) for the train-val-test set 
newTarget=horzcat(Target(:,trainInd),Target(:,valInd),Target(:,testInd)); % % concatenating output values (MoCap data) for the train-val-test set 


Q=numel(traintarget)+numel(validationtarget)+numel(testtarget); 
[net.divideParam.trainInd,net.divideParam.valInd,net.divideParam.testInd] = divideind(Q,1:numel(trainInd),(numel(trainInd)+1):(numel(valInd)...
    +numel(trainInd)),(numel(valInd)+numel(trainInd)+1):(numel(valInd)+numel(trainInd)+numel(testInd))); % passing the train-val-test IDs to the network



net.trainFcn = 'trainlm';  % passing the training function to the network: Levenberg-Marquardt


% % Choose a Performance Function


net.performFcn = 'mse';  % Mean squared error

% % Choose Plot Functions
net.plotFcns = {'plotperform','ploterrhist','plotregression','plotfit'};



net.trainParam.epochs=100; 

% Train the Network
net.trainParam.showWindow=0;
[net,tr] = train(net,newInput,newTarget); %#ok     % training the network 

% Test the Network
outputstrain = net(traininput); % get the network prediction for the training set
outputstest = net(testinput); % get the network prediction for the test set
outputsvalidation = net(validationinput); % get the network prediction for the validation set

errorstrain = gsubtract(traintarget,outputstrain); % calculate the error for the train set predictions
errorstest = gsubtract(testtarget,outputstest); % calculate the error for the test set predictions
errorsvalidation = gsubtract(validationtarget,outputsvalidation); % calculate the error for the validation set predictions





trainrmse {i}(1,j) = sqrt(mean(errorstrain.^2));  % calculate the RMSE for the train set predictions
testrmse {i}(1,j)= sqrt(mean(errorstest.^2)); % calculate the RMSE for the test set predictions
validationrmse {i}(1,j)= sqrt(mean(errorsvalidation.^2)); % calculate the RMSE for the validation set predictions

% saving the trained network

 name1=trial+"_net_P_"+i+"_CV_"+j;
 name2=trial+"_tr_P_"+i+"_CV_"+j;
 % save (name1, 'net')
 % save (name2, 'tr')

clear net
clear tr
    end

     trainPerformance(i)= mean(trainrmse {i}); % claculate the average error over 3-folds for the training set
     testPerformance(i)= mean(testrmse {i}); % claculate the average error over 3-folds for the test set
     validationPerformance(i)= mean(validationrmse {i}); % claculate the average error over 3-folds for the validation set
end
end

