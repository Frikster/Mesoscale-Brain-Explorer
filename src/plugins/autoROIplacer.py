from PyQt4.QtGui import *
from PyQt4.QtCore import *

#This the code for getting the ROI locations from bregma.

#Bregma is (0,0).

#Units are mm.

#ppmm is number of px per millimeter.  Should be 256 px /10.75 mm for last summer.

#ppmm = size(If2,1)/8.6; #user defined
#ii = 1; #clear pos
#
#pos(ii).name = 'M2'; pos(ii).y = 2.5; pos(ii).x = 1; ii = ii + 1;
#pos(ii).name = 'M1'; pos(ii).y = 1.75; pos(ii).x = 1.5;  ii = ii + 1;
#pos(ii).name = 'AC'; pos(ii).y = 0; pos(ii).x = .5; ii = ii + 1;
#pos(ii).name = 'HL'; pos(ii).y = 0; pos(ii).x = 2;  ii = ii + 1;
#pos(ii).name = 'BC'; pos(ii).y = -1; pos(ii).x = 3.5; ii = ii + 1;
#pos(ii).name = 'RS'; pos(ii).y = -2.5; pos(ii).x = .5;  ii = ii + 1;
#pos(ii).name = 'V1'; pos(ii).y = -2.5; pos(ii).x = 2.5; ii = ii + 1;
#
##clear xx yy yy2
#for i = 1:length(pos)
#    xx(i) = yb + -ppmm*pos(i).y;
#    yy(i) = xb - ppmm*pos(i).x;
#    yy2(i) = xb + ppmm*pos(i).x;
#end
#xx = round([xx xx]);
#yy = round([yy yy2]);

class MyPlugin:
  def __init__(self):
    self.name = 'Auto ROI placer'
    self.widget = QWidget()
  
  def run(self):
    pass
