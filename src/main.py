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
from Controllers import dicom_controller

class App(wx.App):
    """subclass of wx.App necessary for main event loop"""
    def onInit(self):
        return True

if __name__ == '__main__':
    """Starts the main event loop for the app"""
    app = App(redirect=False)
    mainFrame = dicom_controller.Controller()
    app.MainLoop()