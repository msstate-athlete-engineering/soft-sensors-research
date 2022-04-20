% This function creates indices for the train-test data for each
% participant. 

% LSTM is sensitive to the length of the sequence and is not capable
% of handling the data in the form of long sequences like a complete trial. Therefore, gait cycles are
% considered as individual sequences of data for training and testing LSTM models.

% Evaluating the performance of LSTM is done with n-fold cross validation. 
% Each participant perform 6 trials and each trial contains 2-3 complete gaits, which provide 12-18 gaits.
% In each fold 3 gaits are considered as the test set and the remaining
% gaits as the training data.

%}
function [Inds] = LSTM_train_test_split (labels)
participant = string.empty(0,numel (labels));

for i = 1:numel(labels)
    participant(i) = unique(labels{i}(1,:)); % get the participant number for each element of "label" array.
end
UniqPar = unique(participant);
Inds = cell(numel(UniqPar),1);  % empty cell array for saving the gait-trials for the train-test sets for each participant

for j = 1:numel(UniqPar) % iterate through participants to split the trials and gaits between train and test set for each participant
    p  =  UniqPar(j);
    Ind =     find(participant == p); % get the gait cycles performed by each participant.
    Ind = Ind(randperm(length(Ind))); % shuffle data
    Inds{j} = cell(ceil(numel(Ind)/3),2); % creating an empty cell for saving the gait cycle indices for the participant j'th 
    
    % If a participant has completed 3 gaits in all the trials (6 trials)
    % then Inds{j} would have 6 rows (as the 6-folds for CV) and each row has two columns in which
    % in the frist ci = olumn with indicate 15 gait cycle IDs for training
    % set and the second column indicates the IDs for the 3 remaining gait
    % cycles which are test set. Each row of the Inds is corresponding to
    % one fold and data are assigned to the train- test sets in each fold
    % so that all the gaits appear at list one time in the test set.
    % In case participants less number of gaits in some trials, there would
    % be 4 or 5 CV. If the last fold does not have three gaits (for exapmle
    % if only 16 or 17 gaits exist, last fold will have 1 or 2 gaits) the remaining
    % gaits will be repeated to preserve consistency in the number of gaits for test set in each fold. 
       
    for i = 1:size(Inds{j},1)
        ii = (3*i-2):min((3*i),numel(Ind));
        if numel(ii) == 2  % in casse only 2 gaits remain for the last fold, the data for the first gait will be repeated to have 3 gaits for the test set.
            ii = horzcat(ii,ii(1));%#ok
        end
        if numel(ii) == 1 % in casse only 1 gaits remain for the last fold, data for this gait will be repeated to have 3 gaits for the test set.
            ii = horzcat(ii,ii,ii);%#ok
        end
    testind = Ind(ii); 
    trainind = Ind((setdiff(1:end,ii)));
    Inds{j}{i,1} = trainind;
    Inds{j}{i,2} = testind;
    end

end
