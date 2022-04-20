% drawing violin plots for RMSE values across various surfaces, foot, 
% methods (Linear regression, ANN, and LSTM), and MoCap outputs (Flexion
% and Inversion)

% RMSE results are saved in a cell array (4,3) called "results", and each cell again is a cell array(1,2) for
% keeping RMSE results from the right and left foot. 
% Each row in the "results" array is related to an specific walking surface Surface and specific output of MoCap. 
% The results from various modeling methods are in 3 columns.

% 4*3 subplots have been created. subplots in each row are corresponding to
% the cells of the "results" array and there are 2 violin plots in each
% subplot for data from left and right foot.


results=cell(4,3);
results {1,1}={FLF_testPerformance_Linear,FRF_testPerformance_Linear};
results {1,2}={FLF_testPerformance_ANN,FRF_testPerformance_ANN};
results {1,3}={FLF_testPerformance_LSTM,FRF_testPerformance_LSTM};

results {2,1}={FLV_testPerformance_Linear,FRV_testPerformance_Linear};
results {2,2}={FLV_testPerformance_ANN,FRV_testPerformance_ANN};
results {2,3}={FLV_testPerformance_LSTM,FRV_testPerformance_LSTM};

results {3,1}={ILF_testPerformance_Linear,IRF_testPerformance_Linear};
results {3,2}={ILF_testPerformance_ANN,IRF_testPerformance_ANN};
results {3,3}={ILF_testPerformance_LSTM,IRF_testPerformance_LSTM};

results {4,1}={ILV_testPerformance_Linear,IRV_testPerformance_Linear};
results {4,2}={ILV_testPerformance_ANN,IRV_testPerformance_ANN};
results {4,3}={ILV_testPerformance_LSTM,IRV_testPerformance_LSTM};



clf
figure 
grid on
space=1.1;
alpha=0.88;
sd=10;
%mtd=["Linear Regression", "ANN", "LSTM"];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Flat surface- Flexion output of MoCap %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

for i=1:3 % Iterate through various methods Linear Regression
for j=1:4
  
ah(1)=subplot(4,3,(j-1)*3+i); 

data_l=results{j,i}{1}'; % getting data for the left foot
data_r=results{j,i}{2}'; % getting data for the right foot


% calculating IQR for the left foot
n=numel(data_l); % number of participants
[y_l,x_l]=hist(data_l);
y_l=smooth(y_l,sd)';
y_l=y_l./max(y_l);
dataR=tiedrank (data_l)./n;
IQR_l=data_l([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% calculating IQR for the right foot
[y_r,x_r]=hist(data_r);
y_r=smooth(y_r,sd)';
y_r=y_r./max(y_r);
dataR=tiedrank (data_r)./n;
IQR_r=data_r([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% plotting the violin plots for the left and right foot and their corresponding mean, median, and IQR 
grid on
hold on
% subtracting or adding space in the following lines are just inserting distance between violin plot for the left and right foot
obj1=patch ([y_l-space -space-y_l(end:-1:1)], [x_l x_l(end:-1:1)], "g", "facealpha", .5); 
obj2=patch ([y_r+space  space-y_r(end:-1:1)], [x_r x_r(end:-1:1)], "b", "facealpha", .5);
obj3=plot ([-space -space], IQR_l, "k", "linew", 3);
obj4=plot (-space, mean (data_l),"ks", "markerfacecolor", "r", "markersize",10);
obj5=plot (-space, median (data_l),"ko", "markerfacecolor", "g", "markersize",10);


set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
plot ([space space], IQR_r, "k", "linew", 3)
plot (space, mean (data_r),"ks", "markerfacecolor", "r", "markersize",10)
plot (space, median (data_r),"ko", "markerfacecolor", "g", "markersize",10)

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
hold off


if j==1  % inserting the title just for the first subplot in each column 
    if i==1
        title ({"Linear Regression"," "},'fontweight','bold','fontsize',24)
    elseif i==2
        title ({"ANN"," "},'fontweight','bold','fontsize',24)
    else
        title ({"LSTM"," "},'fontweight','bold','fontsize',24)
    end
end


set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])

hold off
if i==1 % inserting the y-ticks just for the first subplot in each row (the most left subplot)
    if j==1
        ylabel({"Flexion" , "Flat Surface"," "}  ,'fontweight','bold','fontsize',18)
    elseif j==2
        ylabel({"Inversion" , "Flat Surface"," "} ,'fontweight','bold','fontsize',18)
    elseif j==3    
        ylabel({"Flexion" , "Slopped Surface"," "}  ,'fontweight','bold','fontsize',18)
    elseif j==4
        ylabel( {"Inversion" , "Slopped Surface"," "} ,'fontweight','bold','fontsize',18)
    end

% Setting the legends
hL = legend([obj1,obj2],{'  Left Foot  ','  Right Foot  '} ,'fontweight','bold','fontsize',18,'Orientation','vertical');
newPosition = [0.86 0.6 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
if i==2
hL = legend([obj3,obj4,obj5],{ "  IQR  ", "  Mean  " , "  Median  "} ,'fontweight','bold','fontsize',18);
newPosition = [0.85 0.3 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
end


end