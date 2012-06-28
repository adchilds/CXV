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
        pass

    def center_of_rect(self, x1, y1, x2, y2):
        """ Calculates the center point of the given rect """

        center_x = x1 + (math.fabs(x2 - x1) / 2)
        center_y = y1 + (math.fabs(y1 - y2) / 2)

        return center_x, center_y
    
    def rect_ratio(self, x1, y1, x2, y2):
        """ Calculates the ratio in size between the two given rectangles
        
        @var x1, y1: The smaller rectangle
        @var x2, y2: The larger rectangle
        
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
        print 'Within: %i' % math.fabs(x2 - x1)
        return math.fabs(x2 - x1) <= su
        