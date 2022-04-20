function  [ Data, mainFolder, CSV_filepaths] = Load_data  ()
mainFolder = uigetdir();    % Select your Main folder 
[~,message,~] = fileattrib([mainFolder,'\*']);
fprintf('\n There are %i total files & folders.\n',numel(message));

allExts = cellfun(@(s) s(end-2:end), {message.Name},'uni',0); % Get exts
CSVidx = ismember(allExts,'csv');    % Search ext for "CSV" at the end 

CSV_filepaths = {message(CSVidx).Name};  % Use CSVidx to list all paths.
fprintf('There are %i files with *.CSV exts.\n',numel(CSV_filepaths));

Data = cell(length(CSV_filepaths),1);
for ii = 1:numel(CSV_filepaths)
    
    [~, ~, Data{ii}] = xlsread(CSV_filepaths{ii}); 
    
end

end



