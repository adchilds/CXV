#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Controllers import coral_controller
from Controllers import polyline_controller
from Controllers import calibrate_controller
from Models import polyline_model
import re

class SaveSession():
    
    def __init__(self, controller, path):
        self.controller = controller
        self.update_refs()
        self.path = path
        self.fn_patt = re.compile('(Filename:\s)(.*)')
        self.fn = None  # file name
        self.dw_range_patt = re.compile('(Thickness range:)((\s\d+\.\d+){2})')
        self.dw_range = None
        self.dw_gs_range_patt = re.compile('(AL Grayscale range:)((\s\d+\.\d+){2})')
        self.dw_gs_range = None
        self.dw_gs_patt = re.compile('(Grayscale-to-AL-thick:)((\s-*\d+\.\d+){3})')
        self.dw_gs = None
        self.dw_rgs_patt = re.compile('(Grayscale-to-relative density:)((\s-*\d+\.\d+){3})')
        self.dw_rgs = None
        self.dw_density_patt = re.compile('(Calibration density:\s)(\d+\.\d+)')
        self.dw_density = None
        self.dw_region_patt = re.compile('(Calibration region:)((\s\d+\.\d+){4})')
        self.dw_region = None
        self.cs_patt = re.compile('(Slab Region:)((\s\d+\.\d+){4})')
        self.cs = None  # coral slab
        self.pl_l_patt = re.compile('(Polyline:\st)(\d+)')
        self.pl_l = None# polyline label
        self.pl_patt = re.compile('\d+\.\d+\s\d+\.\d+')
        self.pl = []    # polylines
    
    def update_refs(self):
        self.calibrate_controller = self.controller.calibrate_controller
        self.coral_controller = self.controller.coral_controller
        self.polyline_controller = self.controller.polyline_controller
        
    def read(self):
        file = open(self.path, 'r')
        for line in file:
            try: self.fn = re.match(self.fn_patt, line).group(2)
            except: pass
            try: self.read_calib(line)
            except: pass
            try: self.read_coral_slab(line)
            except: pass
            try: self.read_polylines_label(line)
            except: pass
            try: self.read_polylines(line)
            except: pass
        file.close()
        
    def read_calib(self, line):
        try: self.dw_range = re.match(self.dw_range_patt, line).group(2)
        except: pass
        try: self.dw_gs_range = re.match(self.dw_gs_range_patt, line).group(2)
        except: pass
        try: self.dw_gs = re.match(self.dw_gs_patt, line).group(2)
        except: pass
        try: self.dw_rgs = re.match(self.dw_rgs_patt, line).group(2)
        except: pass
        try: self.dw_density = re.match(self.dw_density_patt, line).group(2)
        except: pass
        try: self.dw_region = re.match(self.dw_region_patt, line).group(2)
        except: pass
        
    def read_coral_slab(self, line):
        self.cs = re.match(self.cs_patt, line).group(2)
        self.cs = self.cs.split(' ')[1:]
        for i in range(len(self.cs)):
            self.cs[i] = float(self.cs[i])
        x, y, w, h = self.cs
        dx = x + w
        dy = y + h
        self.cs = [x, y, dx, dy]
            
    def read_polylines_label(self, line):
        self.pl_l = re.match(self.pl_l_patt, line).group(2)
        self.pl_l = int(self.pl_l)-1
        self.pl.insert(self.pl_l, [])
        
    def read_polylines(self, line):
        self.pl[self.pl_l].append(re.match(self.pl_patt, line).group(0))
        
    def load(self):
        if self.dw_range:
            self.load_calib()
        if self.cs:
            self.load_coral_slab()
        if self.pl:
            self.load_polylines()
        self.controller.draw_all()
        
    def load_calib(self):
        self.controller.calibrate_controller = calibrate_controller.Controller(self.controller.view, self.controller.background)
        self.dw_range = self.dw_range.split(' ')[1:]
        self.controller.calibrate_controller.min_thickness = float(self.dw_range[0])
        self.controller.calibrate_controller.max_thickness = float(self.dw_range[1])
        self.dw_gs_range = self.dw_gs_range.split(' ')[1:]
        self.controller.calibrate_controller.dw_grayscales = [float(self.dw_gs_range[0]),
                                                              float(self.dw_gs_range[1])]
        self.dw_gs = self.dw_gs.split(' ')[1:]
        self.controller.calibrate_controller.dw_linfit = [float(self.dw_gs[0]),
                                                          float(self.dw_gs[1]),
                                                          float(self.dw_gs[2])]
        self.dw_rgs = self.dw_rgs.split(' ')[1:]
        self.controller.calibrate_controller.dw_reldenfit = [float(self.dw_rgs[0]),
                                                             float(self.dw_rgs[1]),
                                                             float(self.dw_rgs[2])]
        self.controller.calibrate_controller.density = float(self.dw_density)
        self.dw_region = self.dw_region.split(' ')[1:]
        tmp = []
        for each in self.dw_region:
            tmp.append(float(each))
        x, y, w, h = tmp
        self.controller.calib_region = [x, y, x+w, y+h]
        self.controller.enable_tools(['Set Density Parameters'], True)
        
        
    def load_coral_slab(self):
        self.controller.coral_controller  = coral_controller.Controller(self.controller.view, self.controller.background)
        self.controller.coral_slab = self.cs
        self.controller.coral_controller.model.sx = self.cs[0]
        self.controller.coral_controller.model.sy = self.cs[1]
        self.controller.coral_controller.model.dx = self.cs[2]
        self.controller.coral_controller.model.dy = self.cs[3]
        self.controller.enable_tools(['Lock Coral Slab', 'Overlay Images'], True)
    
    def load_polylines(self):
        polylines = []
        for each in self.pl:
            polyline = polyline_model.Polyline(self.controller, self.controller.view.axes)
            for coords in each:
                x, y = coords.split(' ')
                x = float(x)
                y = float(y)
                if each.index(coords) != 0:
                    prev_vertex = polyline.get_vertex(each.index(coords)-1)
                    polyline.add_line([prev_vertex.get_xdata()[0], x],
                                      [prev_vertex.get_ydata()[0], y])
                polyline.add_vertex(x, y)
            polylines.append(polyline)
        for polyline in polylines:
            polyline.set_label(polylines.index(polyline))
        self.controller.polyline_controller = polyline_controller.Controller(self.controller, 
                                                                             self.controller.view, 
                                                                             self.controller.background)
        self.controller.polyline_controller.polylines = polylines
        self.controller.polyline_controller.curr_pl = polylines[0]
    
    def write(self):
        self.update_refs()
        file = open(self.path, 'w')
        file.write('Filename: ' + self.controller.model.get_dicom_path()+'\n')
        if self.calibrate_controller: self.write_calib_region(file)
        if self.coral_controller: self.write_coral_slab(file)
        if self.polyline_controller: self.write_polylines(file)
        file.close()
        self.controller.changed = False
        
    def write_calib_region(self, file):
        file.write('Thickness range: ' + str(self.calibrate_controller.min_thickness) + ' ' + str(self.calibrate_controller.max_thickness) + '\n')
        file.write('AL Grayscale range:')
        for each in self.calibrate_controller.dw_grayscales:
            file.write(' ' + str(each))
        file.write('\n')
        file.write('Grayscale-to-AL-thick:')
        for each in self.calibrate_controller.dw_linfit:
            file.write(' ' + str(each))
        file.write('\n')
        file.write('Grayscale-to-relative density:')
        for each in self.calibrate_controller.dw_reldenfit:
            file.write(' ' + str(each))
        file.write('\n')
        file.write('Calibration density: ' + str(self.calibrate_controller.density) + '\n')
        file.write('Calibration region:')
        x, y, dx, dy = self.controller.calib_region
        w = dx-x
        h = dy-y
        coords = [x, y, w, h]
        for coord in coords:
            file.write(' ' + str(coord))
        file.write('\n')
        
    def write_coral_slab(self, file):
        file.write('Slab Region: ')
        x, y, dx ,dy = self.controller.coral_slab
        w = dx - x
        h = dy - y
        slab = (x, y, w, h)
        for coord in slab:
            file.write(str(coord) + ' ')
        file.write('\n')
            
    def write_polylines(self, file):
        for polyline in self.polyline_controller.polylines:
            file.write('Polyline: ' + polyline.label.get_text() + '\n')
            for vertex in polyline.verticies:
                x, = vertex.get_xdata()
                y, = vertex.get_ydata()
                file.write(str(x) + ' ' + str(y) + '\n')