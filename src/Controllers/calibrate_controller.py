#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Models import rectangle_model
from Views import calibrate_view
import math
import numpy as np
import wx

class Controller():

    def __init__(self, dicom_view, background):
        self.dicom_view = dicom_view
        self.model = rectangle_model.Model(self.dicom_view, background, 400, 400, 800, 800)
        self.dicom_view.controller.calib_region = [self.model.sx, self.model.sy, self.model.dx, self.model.dy]
        self.view = calibrate_view.View(self)
        self.density = 2.79
        self.min_thickness = 1.0
        self.max_thickness = 5.0
        self.dw_grayscales = None
        self.dw_linfit = None
        self.dw_reldenfit = None
        
    def on_mouse_motion(self, event):
        self.model.on_mouse_motion(event)
        
    def on_mouse_press(self, event):
        if event.button == 1: # Left click
            pass
        elif event.button == 2: # Scroll-wheel click
            pass
        elif event.button == 3: # Right click
            x, y, w, h = self.model.get_rect_pos()
            if self.model.is_mouse_in_rect(event):
                self.create_popup_menu()
                return
        self.model.on_mouse_press(event)
    
    def on_mouse_release(self, event):
        return self.model.on_mouse_release(event)
        
    def on_pick(self, event):
        self.model.on_pick(event)
            
    def adjust_rect(self, event):
        self.model.adjust_rect(event)
            
    def check_bounds(self):
        self.check_bounds()
        
    def draw_rect(self, adjustable, locked):
        self.model.draw_rect(adjustable, locked, 'b')
        
    def on_density_params(self, event):
        i = 0
        for child in self.view.panel.GetChildren():
            if type(child) == wx._controls.TextCtrl:
                if i == 0:
                    child.SetValue(str(self.density))
                elif i == 1:
                    child.SetValue(str(self.min_thickness))
                elif i == 2:
                    child.SetValue(str(self.max_thickness))
                i += 1
        self.view.Show()
        self.view.Raise()
        
        
    def on_apply(self, event):
        params = []
        for child in self.view.panel.GetChildren():
            if type(child) == wx._controls.TextCtrl:
                params.append(child.GetValue())
        self.density = float(params[0])
        self.min_thickness = float(params[1])
        self.max_thickness = float(params[2])
        self.update_calib_data()
        self.view.Hide()
        self.print_info()
        
    def update_calib_data(self):
        # Load in original dicom pixel data and normalize
        calib_region = self.dicom_view.model.ds.pixel_array.astype(np.double)
        calib_region = self.dicom_view.model.normalize_intensity(calib_region)
        #calib_region = self.dicom_view.model.invert_grayscale(calib_region)

        # Cut down dicom pixel data to user defined calibration region
        x, y, dx, dy = self.dicom_view.controller.calib_region
        calib_region = calib_region[y:dy-1, x:dx-1]

        # Find out which side of the rectangle is longer (width or height)
        if math.fabs(dx - x) > math.fabs(dy - y):
            dw_grayscales = np.mean(calib_region, 1)
        else:
            dw_grayscales = np.mean(calib_region, 0)

        """
        if np.mean(calib_region.std(0, ddof=1)) > np.mean(calib_region.std(1, ddof=1)):
            dw_grayscales = np.mean(calib_region, 1)
        else:
            dw_grayscales = np.mean(calib_region, 0)
        """

        self.dw_grayscales = [dw_grayscales.max(), dw_grayscales.min()]
        b, m, r2 = self.my_least_sq(self.dw_grayscales,
                                    [self.min_thickness, self.max_thickness])
        self.dw_linfit = [b, m, r2]
        b, m, r2 = self.my_least_sq(self.dw_grayscales,
                                    [1., 100.])
        self.dw_reldenfit = [b, m, r2]
        self.dw_grayscales = [dw_grayscales.min(), dw_grayscales.max()]

    def my_least_sq(self, X, Y):
        x = np.ndarray(len(X), np.double)
        for i in range(len(X)):
            x[i] = X[i]
        y = np.ndarray(len(Y), np.double)
        for i in range(len(Y)):
            y[i] = Y[i]
            
        N = len(x)
        sum_x = np.sum(x)
        sum_x2 = np.sum(x*x)
        sum_y = np.sum(y)
        sum_y2 = np.sum(y*y)
        sum_xy = np.sum(x*y)
        sum_xx2 = sum_x2 - ((sum_x**2)/N)
        
        m = (sum_xy - (sum_x*sum_y)/N) / sum_xx2
        b = np.mean(y) - m*np.mean(x)
        
        totalSS = sum_y2 - (sum_y**2)/N
        regSS = m*(sum_xy - (sum_x*sum_y)/N)
        r2 = regSS / totalSS

        return [b, m, r2]
    
    def on_close(self, event):
        self.view.Hide()
        
    def print_info(self):
        print 'Thickness range:', self.min_thickness, self.max_thickness
        print 'AL Grayscale range:', self.dw_grayscales
        print 'Grayscale-to-AL-thick:', self.dw_linfit
        print 'Grayscale-to-relative density:', self.dw_reldenfit
        print 'Calibration density:', self.density
        print 'Calibration region:', self.dicom_view.controller.calib_region
        print

    def create_popup_menu(self):
        self.menu = wx.Menu()
        if not self.dicom_view.controller.calib:
            self.add_option(self.menu, 'Unlock Calibration Region', self.on_popup_item_selected)
        for each in self.popup_line_data():
            self.add_option(self.menu, *each)
        try: self.dicom_view.PopupMenu(self.menu)
        except: pass    # Avoid C++ assertion error
        self.menu.Destroy()
        
    def add_option(self, menu, label, handler):
        option = menu.Append(-1, label)
        self.dicom_view.Bind(wx.EVT_MENU, handler, option)
        
    def popup_line_data(self):
        return [('Lock Calibration Region', self.on_lock_region),
                ('Set Density Parameters', self.on_set_density_params),
                ('Delete Calibration Region', self.delete_calibration)]

    def delete_calibration(self, event):
        self.model = None
        del self.model
        self.dicom_view.controller.calib = False
        self.dicom_view.controller.calibrate_controller = None
        self.dicom_view.controller.enable_tools(['Set Density Parameters'], False)
        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Adjust Calibration Region'], False)

    def on_lock_region(self, event):
        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Adjust Calibration Region'], False)
        self.dicom_view.controller.on_calibrate(event, show=False)

    def on_set_density_params(self, event):
        self.dicom_view.controller.on_density_params(event)

    def on_popup_item_selected(self, event):
        """ Fired when the user selects a popup item on the rectangle model.
        NOTE: If more events are added for different rectangle models, those
        cases will need to be added here. Currently, it will fire all events
        added.
        """
        pass