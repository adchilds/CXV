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
from Views import overlay_view
from lib import progress_bar
import numpy as np
import scipy.ndimage.filters as sp
import math
import re
import wx
import threading

class Controller():
    
    def __init__(self, dicom_view, dicom_controller, model, background, show):
        self.dicom_view = dicom_view
        self.dicom_controller = dicom_controller
        self.model = model
        self.patt = re.compile('\d+')
        self.overlay = None
        self.overlays = [None, None, None]
        self.alphas = [0, 0, 100]
        self.view = overlay_view.View(self, self.dicom_view)
        self.background = background
        self.show = show
        
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
        if self.alphas[0] + self.alphas[1] > 100:
            if i == 0:
                self.alphas[i+1] = 100 - self.alphas[i]
                wx.FindWindowById(self.view.ids[i+1][1]).SetValue(str(self.alphas[i+1])+'%')
                wx.FindWindowById(self.view.ids[i+1][2]).SetValue(self.alphas[i+1])
            else:
                self.alphas[i-1] = 100- self.alphas[i]
                wx.FindWindowById(self.view.ids[i-1][1]).SetValue(str(self.alphas[i-1])+'%')
                wx.FindWindowById(self.view.ids[i-1][2]).SetValue(self.alphas[i-1])
                
            self.alphas[2] = 100 - (self.alphas[0] + self.alphas[1])
        else:
            self.alphas[2] = 100 - (self.alphas[0] + self.alphas[1])

    def create_overlays(self):
        pb = progress_bar.ProgressBar('Creating Overlays', 'Locking coral region', 9, self.dicom_view)
        CreateOverlaysThread(pb, self, self.dicom_controller, self.model)
        
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
        self.dicom_view.canvas.draw()  # cache new axes
        self.dicom_controller.coral_controller.draw_rect(False, True) 
        
    def calc_overlay(self, alphas):
        #use linear combination for displaying overlay
        if not alphas:
            self.overlay = (self.alphas[0]/100.0)*self.overlays[0] + (self.alphas[1]/100.0)*self.overlays[1] + (self.alphas[2]/100.0)*self.overlays[2]
        else:
            self.overlay = (alphas[0]/100.0)*self.overlays[0] + (alphas[1]/100.0)*self.overlays[1] + (alphas[2]/100.0)*self.overlays[2]
        self.overlay = self.model.invert_grayscale(self.overlay)
        
    def display(self, event=None, alphas=None):
        self.calc_overlay(alphas)
        y, x = self.overlay.shape
        rgba, ptr = self.model.allocate_array((y, x, 4))
        rgba = self.model.set_display_data(rgba, self.overlay, 1.0)
        
        self.dicom_view.canvas.restore_region(self.background)
        self.dicom_view.ov_axes.draw_artist(self.dicom_view.ov_axes.imshow(rgba, animated=True))
        self.dicom_view.canvas.blit(self.dicom_view.ov_axes.bbox)
        self.dicom_controller.background = self.dicom_view.canvas.copy_from_bbox(self.dicom_view.axes.bbox)
        self.dicom_controller.draw_all()
        
        self.model.deallocate_array(ptr)
        
class CreateOverlaysThread(threading.Thread):
    
    def __init__(self, pb, controller, dicom_controller, model):
        threading.Thread.__init__(self)
        self.pb = pb
        self.controller = controller
        self.dicom_controller = dicom_controller
        self.model = model
        self.start()
        
    def run(self):
        wx.CallAfter(self.pb.update, 'Retrieving coral region')
        #load in original dicom pixel data and normalize
        coral_slab = self.model.ds.pixel_array.astype(np.double)
        coral_slab = self.model.normalize_intensity(coral_slab)
        #Cut down dicom pixel data to user defined coral slab region
        x, y, dx, dy = self.dicom_controller.coral_slab
        coral_slab = coral_slab[y:dy, x:dx]
        iht, iwd = coral_slab.shape
        wx.CallAfter(self.pb.update, 'Zero padding overlay 1')
        #zero pad image to a power of 2 to speed up FFT
        vpad = 2**(int(math.ceil(math.log(iht, 2))))
        hpad = 2**(int(math.ceil(math.log(iwd, 2))))
        fImg = np.zeros(shape=(vpad, hpad), dtype=np.double, order='C')
        fImg[0:iht, 0:iwd] = coral_slab
        wx.CallAfter(self.pb.update, 'Applying fast fourier transformation to overlay 1')
        #FFT
        fImg = np.fft.fftshift(np.fft.fft2(fImg))
        #find center row and column
        cr = fImg.shape[0]/2
        cc = fImg.shape[1]/2
        #compute distance for every pixel from center
        wx.CallAfter(self.pb.update, 'Computing distance matrix for overlay 1')
        D = np.ones(shape=(vpad, hpad), dtype=np.double, order='C')
        for row in range(iht):
            for col in range(iwd):
                if row==cr and col==cc:
                    wx.CallAfter(self.pb.update, 'Computing distance matrix for overlay 1')
                D[row][col] = math.sqrt((col-cc)**2 + (row-cr)**2)
        D[cr][cc] = 0.00000001  # avoid zero-division warning 
        #Create the Butterworth, high-pass filter
        wx.CallAfter(self.pb.update, 'Creating Butterworth HPF for overlay 1')
        Do = 25
        p = 2
        H = 1/(1 + (Do/D)**(2*p))
        #Highpass filter the source image & strip off the zero-padded regions
        wx.CallAfter(self.pb.update, 'Applying Butterworth HPF to overlay 1')
        fi = H*fImg
        fi = np.fft.ifftshift(fi)
        fi = np.abs(np.fft.ifft2(fi))
        fi = fi[0:iht, 0:iwd]
        #create the overlay
        self.controller.overlays[0] = (coral_slab-fi)
        
        ov2 = np.empty(shape=(iht, iwd), dtype=np.double, order='C')
        wx.CallAfter(self.pb.update, 'Creating sobel filter for overlay 2')
        sp.sobel(coral_slab-fi, output=ov2, mode='nearest')
        ov2 = self.model.normalize_intensity(ov2)
        wx.CallAfter(self.pb.update, 'Applying sobel filter to overlay 2')
        self.controller.overlays[1] = ov2
        self.controller.overlays[2] = coral_slab
        wx.CallAfter(self.pb.finish, 'Finishing up')
        wx.CallAfter(self.controller.add_overlay)
        if self.controller.show:
            self.controller.alphas = [50, 50, 0]
            wx.CallAfter(self.controller.display)
            wx.CallAfter(self.controller.view.Show)
        else:
            wx.CallAfter(self.controller.display)