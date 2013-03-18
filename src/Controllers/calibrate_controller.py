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
from Controllers import polyline_controller
from Models import rectangle_model
from Models import zoom_model
from Views import calibrate_view
import math
import numpy as np
import os
import wx

class Controller():

    def __init__(self, dicom_view, background):
        self.dicom_view = dicom_view
        self.zoom_model = zoom_model.Model()
        x1, y1, x2, y2 = self.zoom_model.get_viewable_rect(self.dicom_view)
        self.model = rectangle_model.Model(self.dicom_view, background, x1+125, y1+125, x1+525, y1+525)
        self.dicom_view.controller.calib_region = [self.model.sx, self.model.sy, self.model.dx, self.model.dy]
        self.unit = 'mm'
        self.pixels_per_unit = ''
        self.density = 2.79
        self.min_thickness = 1.0
        self.max_thickness = 5.0
        self.dw_grayscales = None
        self.dw_linfit = None
        self.dw_reldenfit = None
        self.polyline_controller = None
        self.clicks = 0
        self.click_points = []

        # Setting pixels per unit cursor
        image = wx.Image(self.dicom_view.get_main_dir() + os.sep + "images" + os.sep + "cursor_ppu.png", wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 10) 
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 10)
        self.cursor_ppu = wx.CursorFromImage(image)

        # Instantiate the view last
        self.view = None

    def init_view(self):
        self.view = calibrate_view.View(self, self.unit, self.pixels_per_unit,
                                        self.density, self.min_thickness,
                                        self.max_thickness)
    def on_rotate(self, cx, cy):
        self.model.rotate_lines(cx, cy)
        
    def on_mouse_motion(self, event):
        if self.polyline_controller:
            self.polyline_controller.on_mouse_motion(event)
        else:
            self.model.on_mouse_motion(event)
        
    def on_mouse_press(self, event):
        if self.clicks < 2:
            if self.polyline_controller:
                self.dicom_view.canvas.SetCursor(self.cursor_ppu)
                self.polyline_controller.on_mouse_press(event, False)
                self.click_points.append((event.xdata, event.ydata))
                return

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
        setting_ppu = False
        if self.clicks < 2:
            if self.polyline_controller:
                setting_ppu = True
                self.dicom_view.canvas.SetCursor(self.cursor_ppu)
                self.polyline_controller.on_mouse_release(event)
                if self.clicks + 1 == 2:
                    self.clicks = 0
                    self.polyline_controller = None
                    x1, y1 = self.click_points[0]
                    x2, y2 = self.click_points[1]

                    if self.view is None:
                        self.init_view()

                    if math.fabs(x2 - x1) > math.fabs(y2 - y1):
                        self.view.pixels_per_unit = str(math.fabs(x2 - x1))
                    else:
                        self.view.pixels_per_unit = str(math.fabs(y2 - y1))

                    self.view.tc1.SetValue(self.view.pixels_per_unit)
                    self.view.Show()
                    self.click_points = []
                    self.dicom_view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
                else:
                    self.clicks += 1
        return self.model.on_mouse_release(event, setting_ppu=setting_ppu)
        
    def on_pick(self, event):
        self.model.on_pick(event)
            
    def adjust_rect(self, event):
        self.model.adjust_rect(event)
            
    def check_bounds(self):
        self.check_bounds()
        
    def draw_rect(self, adjustable, locked):
        self.model.draw_rect(adjustable, locked, 'b')
        
    def on_density_params(self, event):
        if self.view is None:
            self.init_view()
        self.view.Show()
        self.view.Raise()

    def on_apply(self, event):
        if self.view is None:
            self.init_view()

        self.unit = self.view.unit_selected[:2]
        self.pixels_per_unit = self.view.tc1.GetValue()
        self.density = self.view.dens.GetValue()
        self.view.wedge_density = self.view.dens.GetValue()
        self.min_thickness = self.view.min.GetValue()
        self.view.min_wedge_thickness = self.view.min.GetValue()
        self.max_thickness = self.view.max.GetValue()
        self.view.max_wedge_thickness = self.view.max.GetValue()
        self.update_calib_data()
        self.view.Hide()

        if len(self.pixels_per_unit) > 0:
            self.dicom_view.controller.set_pixels_per_unit = True
        else:
            self.dicom_view.controller.set_pixels_per_unit = False

        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Set Calibration Parameters'], False)

    def on_set_pixel_unit(self, event):
        if self.view is None:
            self.init_view()
        self.view.Hide()

        self.dicom_view.canvas.SetCursor(self.cursor_ppu)

        self.polyline_controller = polyline_controller.Controller(self.dicom_view.controller, self.dicom_view, self.dicom_view.controller.background, calib=True)
        self.dicom_view.controller.draw_all()
        self.dicom_view.controller.state_changed(True)
        self.dicom_view.controller.calib = True

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
        self.on_apply(event)

    def print_info(self):
        print 'Thickness range:', self.min_thickness, self.max_thickness
        print 'AL Grayscale range:', self.dw_grayscales
        print 'Grayscale-to-AL-thick:', self.dw_linfit
        print 'Grayscale-to-relative density:', self.dw_reldenfit
        print 'Calibration density:', self.density
        print 'Calibration region:', self.dicom_view.controller.calib_region
        print 'Unit selected:', self.unit
        print 'Pixels per unit:', self.pixels_per_unit
        print ''

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
                ('Set Calibration Parameters', self.on_set_density_params),
                ('Delete Calibration Region', self.delete_calibration)]

    def delete_calibration(self, event):
        self.model = None
        del self.model
        self.dicom_view.controller.calib = False
        self.dicom_view.controller.calibrate_controller = None
        self.dicom_view.controller.enable_tools(['Set Calibration Parameters'], False)
        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Adjust Calibration Region'], False)

    def on_lock_region(self, event):
        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Adjust Calibration Region'], False)
        self.dicom_view.controller.on_calibrate(event)

    def on_set_density_params(self, event):
        self.dicom_view.controller.on_density_params(event)

    def on_popup_item_selected(self, event):
        """ Fired when the user selects a popup item on the rectangle model.
        NOTE: If more events are added for different rectangle models, those
        cases will need to be added here. Currently, it will fire all events
        added.
        """
        pass