
     
    
p=8; % selecting the participant
Indcs= IL_Inds{p};  %Get the indices for various trials of an specific Surface-Foot combination
data= IL_inputs;  %Get the indices for various trials of an specific Surface-Foot combination
tit={"Participant 8", "Left Foot - Sloped Surface"}  ; % set the title of plot


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
    newPosition = [0.4 0.4 0.2 0.2];
    newUnits = 'normalized';
    set(hL,'Position', newPosition,'Units', newUnits);
    
    % setting the super title
    sup=suptitle(tit);



