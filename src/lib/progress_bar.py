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
import wx

class ProgressBar(wx.ProgressDialog):
    """Simple sub class of wx.ProgressDialog for various modules to use"""
    def __init__(self, title, first, max, parent):
        wx.ProgressDialog.__init__(self, title, first, max, parent, style=wx.PD_AUTO_HIDE)
        self.counter = 1
        self.max = max
        self.SetSizeWH(400, 150)
        
    def update(self, msg):
        self.Update(self.counter, msg)
        self.counter += 1
        
    def finish(self, msg):
        while self.counter < self.max:
            self.update(msg)
        self.Destroy()