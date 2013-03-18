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
from dxfwrite import DXFEngine as dxf
import wx

class Model():
    """ Contains functions related to DXF file operations in CXV """

    def __init__(self):
        """ Model attributes """

    def create_dxf(self, file_path, polyline_controller, model, calib_controller):
        """ Creates a DXF file at the given 'file_path' location """
        if polyline_controller:
            # Create a DXF object
            drawing = dxf.drawing(file_path)
            points = []

            # Header information
            self.add_header(drawing, '$ACADVER', 'AC1014')

            # Add the polylines
            drawing.add_layer('POLYLINES', color=2)

            # DGZ 16 Aug 2012
            # Bug fix for DXF y-axis flipping error
            # code provided by Adam Childs
            # Convert (0, 0) to bottom-left instead of upper-left for drill program
            #
            sY, sX = model.get_image_shape()

            # Loops through all polylines
            for polyline in polyline_controller.polylines:
                # Loops through all verticies of each polyline
                for vertex in polyline.verticies:
                    try:
                        x = int(vertex.get_xdata())
                        y = int(vertex.get_ydata())
                    except TypeError:
                        # This error is thrown when one of the user's polylines goes outside the coordinates of the image.
                        # For some reason (that I'm not sure of at the moment), the data is put into a 1 element list. So
                        # the fix is to just take the 0th element of the list and then cast it to an integer...
                        # 
                        # Adam Childs (11/17/2012)
                        x = int(vertex.get_xdata()[0])
                        y = int(vertex.get_ydata()[0])

                    y = sY - y
                    
                    x /= float(calib_controller.pixels_per_unit)
                    y /= float(calib_controller.pixels_per_unit)

                    # Set the units in mm
                    if calib_controller.unit == 'cm':
                        x *= 10
                        y *= 10
                    elif calib_controller.unit == 'in':
                        x *= 25.4
                        y *= 25.4

                    points.append((x, y))
                
                # Adds the points to a polyline object, which is added to the DXF file
                drawing.add(dxf.polyline(points))
                points = [] # Reset points for the next polyline to use

            drawing.save()
        else:
            wx.MessageBox('No polylines have been found. Please add some.', 'No polylines!', wx.OK | wx.ICON_ERROR)
            return

    def add_header(self, drawing, header_type, value):
        """ Adds the specified header information to the supplied drawing instance """
        drawing.header[header_type] = value