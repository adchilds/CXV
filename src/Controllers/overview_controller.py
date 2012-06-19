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
from Views import overview_view

class Controller():
    
    def __init__(self, model, dicom_view):
        self.model = model
        self.dicom_view = dicom_view
        self.view = overview_view.View(self, self.model)
        self.canvas = self.view.canvas
        self.axes = self.view.axes
        self.canvas.draw()  # cache clean slate canvas background
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.drag = False
        self.update_viewable_area()
        
    def update_viewable_area(self):
        self.canvas.restore_region(self.background)
        for each in self.calculate_viewable_rect():
            self.draw_viewable_rect(*each)
        self.canvas.blit(self.axes.bbox)
        
    def calculate_viewable_rect(self):
        cx, cy = self.dicom_view.scroll.GetClientSizeTuple()
        cx *= (1.0/self.dicom_view.aspect)
        cy *= (1.0/self.dicom_view.aspect)
        sx, sy = self.dicom_view.scroll.GetViewStart()
        sx *= float(self.dicom_view.scroll.GetScrollPixelsPerUnit()[0])
        sx *= (1.0/self.dicom_view.aspect)
        sy *= float(self.dicom_view.scroll.GetScrollPixelsPerUnit()[1])
        sy *= (1.0/self.dicom_view.aspect)
        if sx == 0.0: sx = 20.0
        if sy == 0.0: sy = 20.0
        return [(cx, cy, sx, sy)]
        
    def draw_viewable_rect(self, cx, cy, sx, sy):
        y, x = self.model.get_image_shape()
        dx = sx+cx
        dy = sy+cy
        if ((dx) > x) and ((dy) > y): # viewable area > x and y image bounds
            self.axes.draw_artist(self.axes.hlines([sy, y-20], sx, x, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.hlines([sy, y-20], sx, x, colors='b', linestyles='solid', linewidth=1, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, x-20], sy, y, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, x-20], sy, y, colors='b', linestyles='solid', linewidth=1, animated=True))
        elif (dx) > x:   # viewable area > x image bounds
            self.axes.draw_artist(self.axes.hlines([sy, dy], sx, x, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.hlines([sy, dy], sx, x, colors='b', linestyles='solid', linewidth=1, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, x-20], sy, dy, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, x-20], sy, dy, colors='b', linestyles='solid', linewidth=1, animated=True))
        elif (dy) > y:   # viewable area > y image bounds
            self.axes.draw_artist(self.axes.hlines([sy, y-20], sx, dx, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.hlines([sy, y-20], sx, dx, colors='b', linestyles='solid', linewidth=1, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, dx], sy, y, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, dx], sy, y, colors='b', linestyles='solid', linewidth=1, animated=True))
        else:   # viewable area < image bounds
            self.axes.draw_artist(self.axes.hlines([sy, dy], sx, dx, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.hlines([sy, dy], sx, dx, colors='b', linestyles='solid', linewidth=1, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, dx], sy, dy, colors='w', linestyles='solid', linewidth=2, animated=True))
            self.axes.draw_artist(self.axes.vlines([sx, dx], sy, dy, colors='b', linestyles='solid', linewidth=1, animated=True))
            
    def on_mouse_motion(self, event):
        if not self.drag: return
        x = event.xdata
        x -= self.mouse_offset_x
        x /= (1.0/self.dicom_view.aspect)
        x /= float(self.dicom_view.scroll.GetScrollPixelsPerUnit()[0])
        y = event.ydata
        y -= self.mouse_offset_y
        y /= (1.0/self.dicom_view.aspect)
        y /= float(self.dicom_view.scroll.GetScrollPixelsPerUnit()[1])
        self.dicom_view.scroll.Scroll(x, y)
        self.update_viewable_area()
    
    def on_mouse_press(self, event):
        x = event.xdata
        y = event.ydata
        cx, cy, sx, sy = self.calculate_viewable_rect()[0]
        if ((x > sx) and (x < sx+cx)) and ((y > sy) and (y < sy+cy)):
            self.mouse_offset_x = x - sx
            self.mouse_offset_y = y - sy
            self.drag = True
    
    def on_mouse_release(self, event):
        self.drag = False
        
    def on_figure_leave(self, event):
        self.drag = False