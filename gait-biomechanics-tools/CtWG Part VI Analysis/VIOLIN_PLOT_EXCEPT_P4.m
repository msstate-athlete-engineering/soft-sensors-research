
clf
figure 
grid on
space=0;
alpha=0.88;
sd=10;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Sloped surface- Flexion output of MoCap- right foot %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

for i=1:3 % Iterate through various methods Linear Regression
for j=3
  
ah(1)=subplot(1,3,i); 


data_r=results{j,i}{2}'; % getting data for the right foot


data_r(4)=[];



% calculating IQR for the right foot
n=numel(data_l); % number of participants
[y_r,x_r]=hist(data_r);
y_r=smooth(y_r,sd)';
y_r=y_r./max(y_r);
dataR=tiedrank (data_r)./n;
IQR_r=data_r([dsearchn(dataR,0.25) dsearchn(dataR,0.75)]);


% plotting the violin plots for the right foot and its corresponding mean, median, and IQR 
grid on
hold on
% subtracting or adding space in the following lines are just inserting distance between violin plot for the left and right foot

obj2=patch ([y_r+space  space-y_r(end:-1:1)], [x_r x_r(end:-1:1)], "b", "facealpha", .5);

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
obj3=plot ([space space], IQR_r, "k", "linew", 3);
obj4=plot (space, mean (data_r),"ks", "markerfacecolor", "r", "markersize",10);
obj5=plot (space, median (data_r),"ko", "markerfacecolor", "g", "markersize",10);

set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])
hold off



    if i==1
        title ({"Linear Regression"," "},'fontweight','bold','fontsize',24)
        ylabel({"Inversion" , "Slopped Surface"," "},  'fontweight','bold','fontsize',20)  % inserting the label for y-axis just for the first subplot in each row (the most left subplot)
    elseif i==2
        title ({"ANN"," "},'fontweight','bold','fontsize',24)
    else
        title ({"LSTM"," "},'fontweight','bold','fontsize',24)
    end




set (gca,'FontSize',12,"Color",[0 0 0]+alpha, "xlim", [-1 1]*(space+2),"ylim", [0 1]*14, "xtick", [])

hold off
if i==1 % inserting the y-ticks just for the first subplot in each row (the most left subplot)
   
        ylabel({"Flexion" , "Slopped Surface"," "}  ,'fontweight','bold','fontsize',18)
        % Setting the legends
        
end


end
if i==2
hL = legend([obj3,obj4,obj5],{ "  IQR  ", "  Mean  " , "  Median  "} ,'fontweight','bold','fontsize',18);
newPosition = [0.85 0.4 0.2 0.2];
newUnits = 'normalized';
set(hL,'Position', newPosition,'Units', newUnits);
end
end

