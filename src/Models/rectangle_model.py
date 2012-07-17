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
import wx

class Model():
    
    def __init__(self, dicom_view, background, sx, sy, dx, dy):
        self.dicom_view = dicom_view
        self.canvas = self.dicom_view.canvas
        self.axes = self.dicom_view.axes
        self.background = background
        self.sx = sx
        self.sy = sy
        self.dx = dx
        self.dy = dy
        self.draw = False
        self.drag = False
        self.adjust = False
        self.picked = ''
        self.left = None
        self.left_adj = None
        
    def on_mouse_motion(self, event):
        if self.drag:
            try:
                self.sx = event.xdata - self.mouse_offset_sx
                self.sy = event.ydata - self.mouse_offset_sy
                self.dx = event.xdata + self.mouse_offset_dx
                self.dy = event.ydata + self.mouse_offset_dy
                self.check_bounds()
            except TypeError:
                pass
        elif self.adjust:
            self.adjust_rect(event)
        else:
            if self.dicom_view.controller.pan_image:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            elif self.dicom_view.controller.zoom:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))
            elif self.left_adj.contains(event)[0] or self.right_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
            elif self.top_adj.contains(event)[0] or self.bottom_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
            elif self.up_left_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
            elif self.low_left_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
            elif self.up_right_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
            elif self.low_right_adj.contains(event)[0]:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
            else:
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        
    def on_mouse_press(self, event):
        self.on_pick(event)
        if (event.xdata > self.sx+20) and (event.xdata < self.dx-20) and (event.ydata > self.sy+20) and (event.ydata < self.dy-20):
            self.drag = True
            self.mouse_offset_sx = event.xdata - self.sx
            self.mouse_offset_sy = event.ydata - self.sy
            self.mouse_offset_dx = self.dx - event.xdata
            self.mouse_offset_dy = self.dy - event.ydata
        elif self.adjust:
            if self.up_left_adj.contains(event)[0]:
                self.picked = 'up_left'
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
            elif self.low_left_adj.contains(event)[0]:
                self.picked = 'low_left'
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
            elif self.up_right_adj.contains(event)[0]:
                self.picked = 'up_right'
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
            elif self.low_right_adj.contains(event)[0]:
                self.picked = 'low_right'
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
            elif self.picked == 'left' or self.picked =='right':
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
            elif self.picked == 'top' or self.picked == 'bottom':
                self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))

    def on_mouse_release(self, event):
        self.drag = False 
        self.adjust = False
        self.dicom_view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        return [self.sx, self.sy, self.dx, self.dy]

    def is_mouse_in_rect(self, event):
        """ Checks whether the user's mouse is within the
        coordinates of the rect.
        """
        return event.xdata >= self.sx and event.xdata <= self.dx and event.ydata >= self.sy and event.ydata <= self.dy

    def get_rect_pos(self):
        return [self.sx, self.sy, self.dx, self.dy]

    def on_pick(self, event):
        if self.left.contains(event)[0]:
            self.adjust = True
            self.picked = 'left'
        elif self.right.contains(event)[0]:
            self.adjust = True
            self.picked = 'right'
        elif self.top.contains(event)[0]:
            self.adjust = True
            self.picked = 'top'
        elif self.bottom.contains(event)[0]:
            self.adjust = True
            self.picked = 'bottom'
            
    def adjust_rect(self, event):
        if (event.xdata is None) or (event.ydata is None): return
        if self.picked == 'left':
            self.sx = event.xdata
        elif self.picked == 'right':
            self.dx = event.xdata
        elif self.picked == 'top':
            self.sy = event.ydata
        elif self.picked == 'bottom':
            self.dy = event.ydata
        elif self.picked == 'up_left':
            self.sx = event.xdata
            self.sy = event.ydata
        elif self.picked == 'low_left':
            self.sx = event.xdata
            self.dy = event.ydata
        elif self.picked == 'up_right':
            self.dx = event.xdata
            self.sy = event.ydata
        elif self.picked == 'low_right':
            self.dx = event.xdata
            self.dy = event.ydata
        self.dicom_view.controller.state_changed(True)
            
    def check_bounds(self):
        iHt, iWd = self.dicom_view.model.get_image_shape()
        if self.sx < 10:
            self.sx = 10
        if self.sy < 10:
            self.sy = 10
        if self.dx > iWd:
            self.dx = iWd-10
        if self.dy > iHt:
            self.dy = iHt-10
        self.dicom_view.controller.state_changed(True)

    def remove_lines(self):
        """ Removes the lines from the axes so that they can be redrawn.
        Stops major memory leak/usage issues.
        """
        try:
            self.left.remove()
            self.right.remove()
            self.top.remove()
            self.bottom.remove()
            self.left_adj.remove()
            self.right_adj.remove()
            self.top_adj.remove()
            self.bottom_adj.remove()
            self.up_left_adj.remove()
            self.low_left_adj.remove()
            self.up_right_adj.remove()
            self.low_right_adj.remove()
        except ValueError:
            pass

    def draw_rect(self, adjustable, locked, color):
        if not locked: c = color
        else: c = 'r'

        # Only need to check these two. If they're true, the others must be as well
        if self.left and self.left_adj:
            '''
            Stops a major memory leak. Program will use TONS of
            memory if we do not remove the old lines when moving
            the rects. By TONS, I mean hundreds of MB, in a matter
            of a few minutes!
            '''
            self.remove_lines()

        self.left = self.axes.vlines([self.sx], self.sy, self.dy, colors=c, linestyles='solid', linewidth=2, picker=1.0, animated=True)
        self.right = self.axes.vlines([self.dx], self.sy, self.dy, colors=c, linestyles='solid', linewidth=2, picker=1.0, animated=True)
        self.top = self.axes.hlines([self.sy], self.sx, self.dx, colors=c, linestyles='solid', linewidth=2, picker=1.0, animated=True)
        self.bottom = self.axes.hlines([self.dy], self.sx, self.dx, colors=c, linestyles='solid', linewidth=2, picker=1.0, animated=True)
        self.axes.draw_artist(self.left)
        self.axes.draw_artist(self.right)
        self.axes.draw_artist(self.top)
        self.axes.draw_artist(self.bottom)
        
        if adjustable:
            wd = (self.dx-self.sx)/2
            ht = (self.dy-self.sy)/2
            size = 7
            self.left_adj, = self.axes.plot([self.sx], [self.sy+ht], c+'s', ms=size, animated=True)
            self.right_adj, = self.axes.plot([self.dx], [self.sy+ht], c+'s', ms=size, animated=True)
            self.top_adj, = self.axes.plot([self.sx+wd], [self.sy], c+'s', ms=size, animated=True)
            self.bottom_adj, = self.axes.plot([self.sx+wd], [self.dy], c+'s', ms=size, animated=True)
            self.up_left_adj, = self.axes.plot([self.sx], [self.sy], c+'s', ms=size, animated=True)
            self.low_left_adj, = self.axes.plot([self.sx], [self.dy], c+'s', ms=size, animated=True)
            self.up_right_adj, = self.axes.plot([self.dx], [self.sy], c+'s', ms=size, animated=True)
            self.low_right_adj, = self.axes.plot([self.dx], [self.dy], c+'s', ms=size, animated=True)     
            
            self.axes.draw_artist(self.up_left_adj)
            self.axes.draw_artist(self.left_adj)
            self.axes.draw_artist(self.low_left_adj)
            self.axes.draw_artist(self.up_right_adj)
            self.axes.draw_artist(self.right_adj)
            self.axes.draw_artist(self.low_right_adj)
            self.axes.draw_artist(self.top_adj)
            self.axes.draw_artist(self.bottom_adj)