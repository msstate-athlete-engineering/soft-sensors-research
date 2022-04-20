% This function generate masks for spliting data to train-validation-test sets from each participant. 
% Each participant perform 6 trials, among them 4 trials have been implemented as the training set, 2 trials for validation and test set.
% This train-vali-test spit will be done 3 times so that each trial will be appear on the val/test set once, therefore there will be 3 sets of masks. 


function [Inds,trials]=splitting_train_test (label)


participant = unique(label(1,:)); % get the participants numbers

Inds=cell(numel(participant),1);    % create an empty cell for storing the masks for spliting data for each participant
trials=cell(numel(participant),1); % create an empty cell for storing the trial names for each train-validation-test set for each participant

for p = 1:numel(participant) % for each participant we separate data for train-validation-test sets. 

    ind=  label(1,:)== participant(p);
    Trial = unique(label(2,ind)); % get trial names
    Trial = Trial(randperm(length(Trial))); % shuffling the trial names 
    Inds{p} = cell((length(Trial)/2),3); % create an 3*3 cell for each participant for storying the masks for 3-fold CV. 
                                       %Each row is for one fold, and there are 3 columns for trian, validation, and test sets.
    trials{p} = Trial; % Storeing the trial names with their order after shufling
for i = 1:(length(Trial)/2) % perform spliting data for each fold
    
    test = Trial(2*i-1); % assign one trial to the test set
    valid = Trial(2*i); % assign one trial to the validation set
    
    testInd = and(label(1,:)== participant(p),strcmp(label(2,:),test));  % get the indices of the samples that are corresponding to the trial which is going to be considered as the test set
    validInd = and(label(1,:)== participant(p),strcmp(label(2,:),valid)); % get the indices of the samples that are corresponding to the trial which is going to be considered as the validation set
    trainInd = and(label(1,:)== participant(p),~or(strcmp(label(2,:),test),strcmp(label(2,:),valid))); % get the indices of the samples that are corresponding to the trial which is going to be considered as the train set

    Inds{p}{i,1} = trainInd; 
    Inds{p}{i,2} = validInd; 
    Inds{p}{i,3} = testInd; 
end
end
    
end
