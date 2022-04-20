function [input,  targetF,  targetV,label,time] =  LSTM_Separate_trials (DataL,SF,pattern)


Ind = find(contains(SF,pattern)); % creat a list of SF elements that belong to the specific Surface-Foot combination (pattern)

input = cell(1,numel(Ind)); % creating input cell for SRS values for trials corresponding to the specific Surface-Foot combination (pattern)
targetF = cell(1,numel(Ind));  % creating targetF cell for the Flexion output of MoCap data for trials corresponding to the specific Surface-Foot combination (pattern)
targetV = cell(1,numel(Ind));  % creating targetV cell for the Inversion output of MoCap data for trials corresponding to the specific Surface-Foot combination (pattern)
label = cell(1,numel(Ind));  % creating label cell for the labels for trials corresponding to the specific Surface-Foot combination (pattern)
time = cell(1,numel(Ind));  % creating time cell for the timestamps for trials corresponding to the specific Surface-Foot combination (pattern)


data =  cellfun(@transpose,DataL,'UniformOutput',false); %transposing the data so that the samples are on the columns


for i = 1:numel(Ind) % iterate through participants to get the info for the trials  corresponding to the specific Surface-Foot combination (pattern)
    ind = Ind(i); % get the indices fir the i'th participant
    input{i} = str2double(data{ind}(4:7,2:end)); % get data in rows 4:7 which are related to the SRS data (input of the LSTM model)
    targetF{i} = str2double(data{ind}(3,2:end)); % get data in row 3 which is related to the Flextion output of MoCap sys(targetF for the LSTM model)
    targetV{i} = str2double(data{ind}(2,2:end)); % get data in row 2 which is related to the Inversion output of MoCap sys(targetV for the LSTM model)
    label{i} = data{ind}(8:11,2:end); % get data in rows 8:11 which are related to the data labels
    time{i} = str2double(data{ind}(1,2:end)); % get data in row 1 which is related to the timestamps
end
        
end




