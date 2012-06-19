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
import wx.grid

class View(wx.MiniFrame):
    
    def __init__(self, controller, model):
        self.controller = controller
        self.model = model
        
        wx.MiniFrame.__init__(self,
                              parent=None,
                              title='Image Information',
                              size=(450, 600),
                              style=wx.DEFAULT_FRAME_STYLE)
        self.Bind(wx.EVT_MOVE, self.controller.dicom_controller.cleanup)
        
        self.grid = SimpleGrid(self, self.model)
        
class SimpleGrid(wx.grid.Grid):
    
    def __init__(self, parent, model):
        wx.grid.Grid.__init__(self, parent, -1)
        self.CreateGrid(len(model.ds), 1)