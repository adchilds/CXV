#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
import math

class Model():
    
    def __init__(self):
        self.view = None

    def center_of_rect(self, x1, y1, x2, y2):
        """ Calculates the center point of the given rect.
        
        @var (x1, y1): the top left corner of the rect
        @var (x2, y2): the bottom right corner of the rect
        """

        center_x = x1 + (math.fabs(x2 - x1) / 2)
        center_y = y1 + (math.fabs(y1 - y2) / 2)

        return center_x, center_y
    
    def rect_ratio(self, x1, y1, x2, y2):
        """ Calculates the ratio in size between the two given rectangles.
        
        @var x1, y1: the smaller rectangle
        @var x2, y2: the larger rectangle
        
        @return: The size ratio between the two rectangles
        """
        if x1 > y1:
            return x2 / x1
        else:
            return y2 / y1

    def within_scroll_unit(self, x1, x2, su):
        """ Returns whether or not the two given points are within 
        one scroll unit of each other.
        
        @var x1: the first point (note: only one axis [x or y])
        @var x2: the second point (note: only one axis [x or y])
        @var su: the scroll unit amount
        """
        print 'Within:', math.fabs(x2 - x1)
        return math.fabs(x2 - x1) <= su

    def get_viewable_rect(self, view):
        """ Calculates the currently viewable portion of
        the image in the wx.ScrolledWindow.
        
        @return: a tuple with (x1, y1) as top-left
                 and (x2, y2) as bottom-right.
        """
        self.view = view
        cx, cy = self.view.scroll.GetClientSizeTuple()
        cx *= (1.0/self.view.aspect)
        cy *= (1.0/self.view.aspect)
        sx, sy = self.view.scroll.GetViewStart()
        sx *= float(self.view.scroll.GetScrollPixelsPerUnit()[0])
        sx *= (1.0/self.view.aspect)
        sy *= float(self.view.scroll.GetScrollPixelsPerUnit()[1])
        sy *= (1.0/self.view.aspect)
        sx = int(sx)
        sy = int(sy)
        cx = int(cx) + sx
        cy = int(cy) + sy
        return [sx, sy, cx, cy]
        