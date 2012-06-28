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
from Controllers import plugin_controller
from Controllers import xml_controller
from lib import progress_bar
from Views import overlay_view
from yapsy.PluginManager import PluginManager
import numpy as np
import scipy.ndimage.filters as sp
import math
import os
import re
import wx
import threading

class Controller():
    
    def __init__(self, dicom_view, dicom_controller, model, background, show):
        self.dicom_view = dicom_view
        self.dicom_controller = dicom_controller
        self.model = model
        self.patt = re.compile('\d+')
        self.overlay = 0.0
        self.overlays = []
        self.alphas = []
        self.view = overlay_view.View(self, self.dicom_view)
        self.background = background
        self.show = show

    def getPluginCount(self):
        # Get the default plugin directory, using XML
        path = os.path.expanduser('~')
        xml = xml_controller.Controller(path + '\.cxvrc.xml')
        xml.load_file()
        xml.get_plugin_directory()
        directory = ["plugins", xml.get_plugin_directory()]

        # Load the plugins from the plugin directory.
        manager = PluginManager()
        manager.setPluginPlaces(directory)
        manager.setPluginInfoExtension('plugin')
        manager.collectPlugins()
        
        return len(manager.getAllPlugins())
        
    def find_items(self, event):
        for tuple in self.view.ids:
            for id in tuple:
                if id == event.GetId():
                    i = self.view.ids.index(tuple)  # 0=ov1, 1=ov2, 2=base
                    cb = wx.FindWindowById(tuple[0])
                    tc = wx.FindWindowById(tuple[1])
                    s = wx.FindWindowById(tuple[2])
        if type(wx.FindWindowById(event.GetId())) == wx._controls.CheckBox:
            self.on_checkbox(i, cb, tc, s)
        elif type(wx.FindWindowById(event.GetId())) == wx._controls.TextCtrl:
            self.on_text_ctrl(i, tc, s)
        self.on_slider(i, s, tc)
        
    def on_checkbox(self, i, cb, tc, s):
        if cb.GetValue():
            tc.Enable(True)
            s.Enable(True)
        else:
            tc.Enable(False)
            tc.SetValue('0%')
            s.Enable(False)
            s.SetValue(0)
            self.alphas[i] = 0
    
    def on_text_ctrl(self, i, tc, s):
        m = self.patt.match(tc.GetLabel())  # match = start of string only
        if m is None:
            tc.SetValue(str(self.alphas[i]) + '%')
        else:
            if int(m.group(0)) > 100:
                self.alphas[i] = 100
                tc.SetValue('100%')
            else:
                self.alphas[i] = int(m.group(0))
                tc.SetValue(str(int(m.group(0)))+'%')
        s.SetValue(self.alphas[i])

    def on_slider(self, i, s, tc):
        self.alphas[i] = s.GetValue()
        tc.SetValue(str(self.alphas[i]) + '%')

        total_alphas = 0
        for a in range(len(self.alphas) - 1):
            total_alphas += self.alphas[a]

        if total_alphas > 100:
            for m in range(len(self.alphas) - 1):
                if m is not i: # if m is not equal to the alpha slider we're moving
                    self.alphas[m] = 100 - (total_alphas - self.alphas[m])
                    if self.alphas[m] < 0:
                        self.alphas[m] = 0
                    wx.FindWindowById(self.view.ids[m][1]).SetValue(str(self.alphas[m])+'%')
                    wx.FindWindowById(self.view.ids[m][2]).SetValue(self.alphas[m])                    
            self.alphas[len(self.alphas) - 1] = 0
        else:
            self.alphas[len(self.alphas) - 1] = 100 - total_alphas

        # Just in case, lets check these
        if self.alphas[len(self.alphas) - 1] < 0:
            self.alphas[len(self.alphas) - 1] = 0
        elif self.alphas[len(self.alphas) - 1] > 100:
            self.alphas[len(self.alphas) - 1] = 100

    def create_overlays(self):
        """ Initializes the progress bar.
        
        Sets the total number of progress bar units to the total
        ((number of plugins * 2) + 1) for the initial progress bar message
        (This means that each plugin should send an update message twice; once
        each for beginning and ending the algorithm).
        
        Initializes the plugin controller, which then runs the plugin algorithms.
        """
        pb = progress_bar.ProgressBar('Creating Overlays', 'Locking coral region', ((self.getPluginCount() * 2) + 1), self.dicom_view)
        plugin_controller.Controller(pb, self, self.dicom_controller, self.model)

    def add_overlay(self):
        x, y, dx, dy = self.dicom_controller.coral_slab
        iH, iW = self.model.get_image_shape()
        x = float(x)
        y = float(y)
        dx = float(dx)
        dy = float(dy)
        iH = float(iH)
        iW = float(iW)
        l = x/iW
        b = 1.0 - (dy/iH)
        w = (dx-x)/iW
        h = (dy-y)/iH
        
        self.dicom_view.ov_axes = self.dicom_view.figure.add_axes((l,b,w,h))
        self.dicom_view.ov_axes.set_axis_off()
        self.dicom_view.ov_axes.patch.set_facecolor('none')
        self.dicom_view.canvas.draw() # cache new axes
        self.dicom_controller.coral_controller.draw_rect(False, True)

    def calc_overlay(self, alphas):
        """ Calculates the visible overlay, depending on the transparency
        levels set for each of the overlays.
        """
        # Use linear combination for displaying overlay
        self.overlay = 0.0 # Reset to 0.0; if we don't the new overlays are appended to the old!
        if not alphas:
            for ov in range(len(self.overlays)):
                self.overlay += (self.alphas[ov]/100.0) * self.overlays[ov]
        else:
            for ov in range(len(self.overlays)):
                self.overlay += (alphas[ov]/100.0) * self.overlays[ov]
        self.overlay = self.model.invert_grayscale(self.overlay)

    def display(self, event=None, alphas=None):
        self.calc_overlay(alphas)
        y, x = self.overlay.shape
        rgba, ptr = self.model.allocate_array((y, x, 4))
        rgba = self.model.set_display_data(rgba, self.overlay, 1.0)

        # Restore the canvas to what the background should be. Otherwise, when re-opening
        # the overlay view after it's been closed, and we're zoomed in, the zoom to fit
        # background is shown over our zoomed image.
        self.dicom_view.canvas.restore_region(self.dicom_controller.background)
        self.dicom_view.ov_axes.draw_artist(self.dicom_view.ov_axes.imshow(rgba, animated=True))
        self.dicom_view.canvas.blit(self.dicom_view.ov_axes.bbox)
        self.dicom_controller.background = self.dicom_view.canvas.copy_from_bbox(self.dicom_view.axes.bbox)
        self.dicom_controller.draw_all()

        self.model.deallocate_array(ptr)