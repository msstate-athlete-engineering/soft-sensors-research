function [ trainPerformance,testPerformance, trainrmse, testrmse ] = LinearModeling (Input,Target,Inds)
trainrmse= cell(1,size (Inds,1));  % cell array for saving the RMSE values for train set
testrmse= cell(1,size (Inds,1));  % cell array for saving the RMSE values for test set
    
trainPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over 3-fold for train set.
testPerformance= zeros(1,size (Inds,1)); % array for saving the average rmse values over 3-fold for test set.

% Iterate through each participant's indices     
for i = 1:size (Inds,1) % same Inds is utilized for the ANN and Linear regression
    
    Indcs= Inds{i}; % Indcs is a 3*3 cell. each row is corresponding to each fold 
                    % and first column is corresponding to the train set
                    % indices, second column corresponding to the validation set
                    % third column is coressponding to the test set.
    
    % Iterate through each trial within that participant and assign 
    % training/testing data
    
    for j=1:size(Indcs,1)
        % Stretchsense Input
        traininput= Input(:,Indcs{j,1}); % getting the input values (SRS data) for the training set
        testinput1= Input(:,Indcs{j,2}); % getting the input values (SRS data) for the validation set
        testinput2= Input(:,Indcs{j,3}); % getting the input values (SRS data) for the test set
        testinput= horzcat (testinput1,testinput2); % linear regression doesn't need validation set, therefore data for the test and validation sets 
                                                    % are joined together and will be considered as the test set.
                                      
    
        % Motion Capture Output
        traintarget= Target(Indcs{j,1}); % getting the output values (Mocap data) for the training set
        testtarget1= Target(Indcs{j,2}); % getting the output values (Mocap data) for the validation set
        testtarget2= Target(Indcs{j,3}); % getting the output values (Mocap data) for the test set
        testtarget= horzcat( testtarget1,testtarget2);% linear regression doesn't need validation set, therefore data for the test and validation sets 
                                                    % are joined together and will be considered as the test set.
        % Generate linear model based on training (4 Trials) record 
        % Use all four inputs to predict
        lm = fitlm(traininput', traintarget', 'linear');
        trainrmse {i}(1,j) = lm.RMSE;

        % Test the linear model
        % run linear model and record RMSE
        outputstest = predict(lm, testinput');
        errorstest = gsubtract(testtarget,outputstest');
        testrmse {i}(1,j)= sqrt(mean(errorstest.^2));
    end

     trainPerformance(i)= mean(trainrmse {i}); % claculate the average error over 3-folds for the training set
     testPerformance(i)= mean(testrmse {i}); % claculate the average error over 3-folds for the test set
end
end

