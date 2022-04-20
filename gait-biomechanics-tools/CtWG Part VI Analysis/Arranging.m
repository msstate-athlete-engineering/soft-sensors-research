function [DataL,SF]= Arranging(Data,mainFolder, CSV_filepaths)
SF = strings(1,numel(CSV_filepaths));

 % CSV_filepats contains the information about the participant, foot,
 % trial (including walking surface), and gait. These information are extracted from the
 % CSV_filepaths string and 4 new columns are added to the data regarding these features. 
 
DataL=cell(size(Data,1),1);
for ii = 1:numel(CSV_filepaths) %Iterate through gait cycles data stored on the cells of "Data" cell array extracting the information and creating new columns.  
    
    newStr = string(extractBetween(CSV_filepaths{ii},length (mainFolder)+2, length (mainFolder)+5  ));     % extracting participant number                                            
    ParticipantName= ['Participant Name';repmat(newStr,size(Data{ii},1)-1,1)]; % creating a new column for participant number
    
    newStr2 = string(extractBetween(CSV_filepaths{ii},length (mainFolder)+7,length(CSV_filepaths{ii})-14)); % extracting trial name
    TrialName=['Trial Name';repmat(newStr2,size(Data{ii},1)-1,1)];  % creating a new column for trial name
    
    newStr3 = string(extractBetween(CSV_filepaths{ii},length(CSV_filepaths{ii})-12,length(CSV_filepaths{ii})-11)); % extracting foot (left/right)
    Foot=['Foot';repmat(newStr3,size(Data{ii},1)-1,1)];  % creating a new column for foot
    
    newStr4 = string(extractBetween(CSV_filepaths{ii},length(CSV_filepaths{ii})-10,length(CSV_filepaths{ii})-4)); % extracting gait number
    Gait=['Gait';repmat(newStr4,size(Data{ii},1)-1,1)]; % creating a new column for gait number
    
    DataL{ii}=[(Data{ii}),ParticipantName,TrialName,Foot,Gait]; % Adding new 4 columns to the data
    
    % creating SF array which indiates each cell of Data file belongs to which Surface-Foot combination including:
   
    % FR:Flat surface-Right foot
    % FL:Flat surface-Left foot
    % IR:Inclined surface-Right foot
    % IL:Inclined surface-Left foot
    
    patternF="RF"; % variable for checking the foot, RF: right foot
    patternT="INV";  % variable for checking the trial, INV indicates the trials related to the inclined surface
   
    if and(contains(newStr2,patternT),contains(newStr3,patternF))
        SF(ii)= "IR";
       
        
    elseif and(contains(newStr2,patternT),~contains(newStr3,patternF))
        SF(ii)= "IL";
      
        
    elseif and(~contains(newStr2,patternT),contains(newStr3,patternF))
        SF(ii)= "FR";
       
        
    elseif and(~contains(newStr2,patternT),~contains(newStr3,patternF))
        SF(ii)= "FL";
      
        
    end
 end 




end
