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
from Models import rectangle_model

class Controller():
    
    def __init__(self, dicom_view, background):
        self.dicom_view = dicom_view
        self.model = rectangle_model.Model(self.dicom_view, background, 200, 200, 600, 600)
        self.dicom_view.controller.coral_slab = [self.model.sx, self.model.sy, self.model.dx, self.model.dy]
        
    def on_mouse_motion(self, event):
        self.model.on_mouse_motion(event)
        
    def on_mouse_press(self, event):
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
        self.model.draw_rect(adjustable, locked, 'y')