function draw_binary_image
% left click: draw wall
% right click: draw floor
% middle click: draw food
% 'p': print ascii map

dims = [20 20];

FLOOR = 3;
WALL = 1;
FOOD = 2;
cmap = [];
cmap(FLOOR,:) = [0.5 0.3 0.1];
cmap(WALL,:) = [0.2 0.2 0.8];
cmap(FOOD,:) = [1 1 1];



map = FLOOR*ones(dims);
clf
ud.h = figure(1)
ud.ax = update_graphics(map,cmap)

ud.cmap = cmap;
ud.isdown = 0;
ud.map = map;
ud.dims = dims;
set(ud.h,'WindowButtonMotionFcn',@motionfun);
set(ud.h,'WindowButtonUpFcn',@upfun);
set(ud.ax,'ButtonDownFcn',@downfun);
set(ud.h,'KeyPressFcn',@kbd_function);

set(ud.h,'UserData',ud);


function kbd_function(src,evnt)
hfig = gcf;
ud = get(hfig,'UserData');
switch evnt.Key
    case 'p'
        print_map(ud.map);
end


function print_map(map)
c = {'%','*','.'};
fprintf('\n\n\nrows %d\ncols %d\nplayers 0\n',size(map,1),size(map,2))
for y=1:size(map,1)
    fprintf('m ');
    for x=1:size(map,2)
        fprintf('%s',c{map(y,x)});
    end
    fprintf('\n');
end

function motionfun(src,eventdata)
ud = get(gcf,'UserData');
if ud.isdown
    do_labeling();
end

function downfun(src,eventdata)
s.normal = 1;
s.extend = 2;
s.alt = 3;
ud = get(gcf,'UserData');
stype = get(get(get(src,'Parent'),'Parent'),'SelectionType');
ud.isdown = s.(stype);
set(gcf,'UserData',ud);
0;

function upfun(src,eventdata)
do_labeling();
ud = get(gcf,'UserData');
ud.isdown = 0;
set(gcf,'UserData',ud);
0;
 
function do_labeling()
ud = get(gcf,'UserData');

%skips race condiiton:
if ~ishandle(ud.ax), return, end

pt = get(get(ud.ax,'Parent'),'CurrentPoint');
pt = round(pt(1,1:2))';
btn = ud.isdown;



if any(pt < 1) || any(pt > ud.dims([2 1])')
    return
end

if ud.map(pt(2),pt(1)) ~= btn
    ud.map(pt(2),pt(1)) = btn;
    ud.ax = update_graphics(ud.map,ud.cmap);
    set(ud.ax,'ButtonDownFcn',@downfun);
end
set(gcf,'UserData',ud);


function ax = update_graphics(map,cmap)
cla
subplot(1,1,1), ax = imagesc(ind2rgb(map,cmap));
colormap(cmap)
axis image
set(gca,'YTick',(1:size(map,1))+0.5)
set(gca,'XTick',(1:size(map,2))+0.5)
grid on
drawnow

