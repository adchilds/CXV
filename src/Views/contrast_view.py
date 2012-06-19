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
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import wx
import numpy as np

class View(wx.MiniFrame):
    
    def __init__(self, controller, dicom_view, model):
        self.controller = controller
        self.model = model
        
        wx.MiniFrame.__init__(self,
                              parent=dicom_view,
                              title='Contrast Tool',
                              size=(550, 250),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.init_plot()
        self.histogram()
        self.Show()
        
    def histogram(self):
        img = self.model.ds.pixel_array.astype(np.double)
        img -= img.min()
        img /= img.max()
        img = 1 - img
        img = img.flatten()
        self.axes.hist(img, 1000, range=(0.0,1.0))
        
    def init_plot(self):
        self.figure = Figure()
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.axes = self.figure.add_axes([0.0, 0.0, 1.0, 1.0])