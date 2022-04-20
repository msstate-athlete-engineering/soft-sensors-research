% This function aggregate all the data from various participants and trials with an specific surface-foot
% combination to a single file. 


% This function gets 3 inputs including Data cell array, SF array which
% indicates Surface-Foot combination for each cell in the "DataL" cell array, 
% and an specific surface-foot pattern: including "FR", "FL", "IR", "IL".


% This function creates following matrices as the outputs:

% One matrix for the SRS data as: "input"
% One matrix for the Flexion output of MoCap sys as: Ftarget
% One matrix for the Inversion output of MoCap sys as: Vtarget
% One matrix for the 4 label columns including participant number, trial, foot, and gait as: label
% One matrix for the timestamps as: time



function [input, Ftarget, Vtarget,label, time]      = Separate_trials (DataL, SF, pattern)

 
Ind=find(contains(SF,pattern)); %creat a list of SF elements that belong to the specific Surface-Foot combination (pattern)

Psize=0; % varriable indicating the total number of samples for the specific pattern
for i=Ind % Iterate through the cells with the specific pattern of interest and get the number of time stamps and add up them together
    
Psize=Psize+ (size(DataL{i},1)-1);

end

Ag_data=strings (size(DataL{i},2),Psize(1)); % Creat an empty matrix for data which has 4 rows for SRS data (size(DataL{i},2)) and "Psize(1)" columns (total number of samples for the specific pattern).

data= cellfun(@transpose,DataL,'UniformOutput',false); % transposing the data in each cell

% Stacking data from the cells corresponding to the specific pattern of interest innto a new file: Ag_data 

s=1;
f=0;

for j = Ind  
    
    D =  data {j}(:,2:end);  
    f=f+size(D,2);   
    Ag_data (:,s:f)=D; 
    s=f+1;

end

time=str2double(Ag_data(1,:)); % Getting the first column of Ag_data which is the timestamps and inserting it in the time martix

Vtarget=str2double(Ag_data(2,:)); % Getting the second column of Ag_data which is the Inversion output of MoCap sys and inserting it in the Vtarget martix

Ftarget=str2double(Ag_data(3,:)); % Getting the third column of Ag_data which is the Flexion output of MoCap sys and inserting it in the Ftarget martix

input=str2double(Ag_data(4:7,:)); % Getting the columns 4 to 7 of Ag_data which are SRS data and inserting it in the input martix

label=Ag_data(8:11,:); % Getting the columns 8 to 11 of Ag_data which are labels and inserting it in the label martix

end




