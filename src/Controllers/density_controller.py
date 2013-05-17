import collections
import math
import numpy as np
import random
import wx
from scipy import stats
from Views import density_view

class Controller():

    def __init__(self, dicom_controller, arr=[]):
        self.dicom_controller = dicom_controller
        self.averages = arr
        self.all_lines = []
        self.lines = []
        self.lines_names = []
        self.lines_colors = []
        self.colors = ["#000000", "#FF6600", "#339900", "#FF3399", "#0066CC", "#CCFF00",
                       "#66CC99", "#003300", "#33CCFF", "#FFCCCC", "#990000", "#003333"]
        self.removed_lines = []
        self.removed_lines_names = []
        self.removed_lines_colors = []
        self.view = density_view.View(self, arr)
        self.view.Show()

    def lin_regress(self, arr, line=True):
        """ Calculates the linear regression line of the array provided
        
        @return the line if bool is True
        @return the slope, intercept, etc that make up the line if bool is False
        """
        x = np.arange(0, len(arr))
        
        slope, intercept, r_value, p_value, std_dev = stats.linregress(x, arr)

        if line: # return an array of values that make up the regression line
            return slope * x + intercept
        return slope, intercept

    def grayscale_to_thickness(self, gs):
        """ Calculates the equivalent aluminum thickness for
        a given grayscale value
        
        @param gs The grayscale value
        """
        
        # Calculate slope and intercept of linear regression line of wedge column averages
        m, b = self.lin_regress(self.averages, False)
        
        # Calculate which column, in our regression line, the grayscale value is
        # x = column #
        x = (gs - b) / m

        # Calculate slope of wedge
        max_thick = float(self.dicom_controller.calibrate_controller.max_thickness)
        min_thick = float(self.dicom_controller.calibrate_controller.min_thickness)
        x1 = self.dicom_controller.calibrate_controller.model.sx
        x2 = self.dicom_controller.calibrate_controller.model.dx
        length = math.fabs(x1 - x2)
        m = (min_thick - max_thick) / length
        
        # Calculate intercept of wedge
        b = max_thick

        return (m * x) + b

    def plot_line(self, arr):
        """ Plots the given array arr as a line on the Density View's subplot """
        self.view.plot(arr)
        self.view.axes.set_xlim(0 - 5, len(arr) + 5)
        self.view.axes.set_ylim(min(arr) - 5, max(arr) + 5)
        self.view.axes.set_yticks(np.arange(int(min(arr)) - 5, int(max(arr)) + 5, 10))
        self.view.canvas.draw()

    def bresenham_line(self, x0, y0, x1, y1):
        """ Calculates the bresenham line between two given points on the
            geometry plane. Essentially, draws a straight line from A - B,
            giving the coordinates in between.
                
            Algorithm (Simplicity section):
            http://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
                
            @param x0, y0 - Starting point
            @param x1, y1 - End point
        """
        coords = []
        dx = math.fabs(x1 - x0)
        dy = math.fabs(y1 - y0)
        if x0 < x1:
            sx = 1
        else:
            sx = -1
        if y0 < y1:
            sy = 1
        else:
            sy = -1
        err = dx - dy
        while True:
            coords.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err = err - dy
                x0 = x0 + sx
            if x0 == x1 and y0 == y1:
                coords.append((x0, y0))
                break
            if e2 < dx:
                err = err + dx
                y0 = y0 + sy
        return coords

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                for sub in self.flatten(el):
                    yield sub
            else:
                yield el

    def calc_graph(self):
        polyline_data = [] # Holds all polylines after the data has been pulled out
        self.lines_names = []
        for polyline in self.dicom_controller.polyline_controller.polylines:
            i = 1
            xPrev = 0
            yPrev = 0
            temp = [] # Holds each individual polyline temporarily
            for vertex in polyline.verticies:
                x, = vertex.get_xdata()
                y, = vertex.get_ydata()
                
                if i % 2 == 0: # Every other loop (every other line)
                    temp.append(self.bresenham_line(int(xPrev), int(yPrev), int(x), int(y)))
                i += 1
                xPrev = x
                yPrev = y
            polyline_data.append(temp)

        # Example of array structure
        # polyline_data = [ [pl1 [ ] [ ] [ ] ] , [pl2 [ ] [ ] ] , [pl3 [ ] [ ] [ ] [ ] ] ]
        # Join together all sub-arrays per polyline
        for i in xrange(len(polyline_data)):
            polyline_data[i] = list(self.flatten(polyline_data[i]))

        # Get the grayscale value of each pixel
        grayscales = []
        for pl in polyline_data:
            temp = []
            flag = False
            for x in xrange(len(pl)):
                if flag:
                    flag = False
                    continue
                # Get grayscale value at pixel (x,x+1)
                gs = self.dicom_controller.model.image_array[pl[x+1]][pl[x]][0] # y, x

                # Append grayscale to temp array
                new_value = ( (gs - 0) / (1 - 0) ) * (255 - 0) + 0
                temp.append(int(new_value))
                
                # Set flag so that we will skip next loop iteration
                flag = True
            grayscales.append(temp)

        max_val = float(self.dicom_controller.calibrate_controller.max_thickness)
        min_val = float(self.dicom_controller.calibrate_controller.min_thickness)

        # Convert each grayscale to equivalent aluminum thickness
        for pl in grayscales:
            for x in xrange(len(pl)):
                val = self.grayscale_to_thickness(pl[x])
                if val > max_val or val < min_val:
                    val = np.NAN
                pl[x] = val
                
        # Flip the values
        for pl in grayscales:
            for x in xrange(len(pl)):
                pl[x] = max_val - pl[x] + min_val

        self.lines = grayscales
        self.all_lines = [ [] for x in xrange(len(self.lines)) ]
        for x in xrange(len(self.lines)):
            name = "t" + str(int(x+1))
            self.all_lines[x].append(name) # name
            self.all_lines[x].append(self.lines[x]) # line_data
            try:
                self.all_lines[x].append(self.colors[x]) # color
            except: # No more available colors
                r = lambda: random.randint(0, 255)
                c = '#%02X%02X%02X' % (r(), r(), r())
                self.all_lines[x].append(c) # color
            self.all_lines[x].append(True) # bool

            self.lines_names.append("t" + str(x+1))
            try:
                self.lines_colors.append(self.colors[x])
            except: # No more available colors
                r = lambda: random.randint(0, 255)
                c = '#%02X%02X%02X' % (r(), r(), r())
                self.lines_colors.append(c)

        return grayscales

    def on_close(self, event):
        """ Hides the Density View """
        self.view.Destroy()
        self.dicom_controller.density_controller = None

    def on_export_image(self, event):
        """
        Grabs the graph in the viewport and saves it as an
        image in the user's current directory.
        """
        dialog = wx.FileDialog(self.view, "Export Image", style=wx.SAVE|wx.OVERWRITE_PROMPT, wildcard='Portable Network Graphic (*.png)|*.png')
        dialog.SetFilename(str(self.view.controller.dicom_controller.file_name))

        if dialog.ShowModal() == wx.ID_OK:
            # Is the user saving a CXV Session file or XML file?
            path = dialog.GetPath()
            self.view.figure.savefig(path)
        
    def on_export_graph(self, event):
        dialog = wx.FileDialog(self.view, "Export Data File", style=wx.SAVE|wx.OVERWRITE_PROMPT, wildcard='Data File (*.txt)|*.txt')
        dialog.SetFilename(str(self.view.controller.dicom_controller.file_name))

        if dialog.ShowModal() == wx.ID_OK:
            # Is the user saving a CXV Session file or XML file?
            path = dialog.GetPath()
            data_file = open(path, 'w')
            data_file.write("NOTE: \"nan\" stands for \"not a number.\" The value was not able to be computed.\n")
            data_file.write("---------------------------------------------------------------------------------\n\n\n")
            i = 1
            for pl in self.calc_graph():
                data_file.write("Polyline t" + str(i) + ":\n")
                for item in pl:
                    data_file.write("%s, " % item)
                data_file.write("\n\n")
                i += 1
            data_file.close()