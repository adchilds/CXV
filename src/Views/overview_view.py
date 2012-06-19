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
from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

class View(wx.MiniFrame):
    
    def __init__(self, controller, model):
        self.controller = controller
        self.model = model
        
        wx.MiniFrame.__init__(self,
                              parent=None,
                              title="Overview",
                              size=(300, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        x, y = self.GetSizeTuple()
        self.figure = plt.figure(figsize=(x/72.0, y/72.0), dpi=72)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.axes = self.figure.add_axes([0.0, 0.0, 1.0, 1.0])
        self.axes.imshow(self.model.get_image(), aspect='auto')
        self.axes.set_axis_off()
        self.mpl_bindings()
        self.Bind(wx.EVT_MOVE, self.controller.dicom_view.controller.cleanup)
        self.Show()
        
    def mpl_bindings(self):
        for each in self.mpl_binds():
            self.connect(*each)
            
    def connect(self, event, handler):
        self.canvas.mpl_connect(event, handler)
            
    def mpl_binds(self):
        return ( ('motion_notify_event', self.controller.on_mouse_motion),
                 ('button_press_event', self.controller.on_mouse_press),
                 ('button_release_event', self.controller.on_mouse_release),
                 ('figure_leave_event', self.controller.on_figure_leave)
               )
        