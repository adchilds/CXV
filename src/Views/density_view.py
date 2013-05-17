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
import wx
import wx.lib.scrolledpanel as sp

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

class View(wx.Frame):
    
    def __init__(self, controller, arr=[]):
        # The frame
        wx.Frame.__init__(self,
                              parent=None,
                              title="Density Chart",
                              style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.controller = controller
        self.lines = arr
        self.density_panel = None # Holds our density parameter widgets

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left panel
        self.left_panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        
        # Right panel
        self.right_panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        top = right_top_panel(self.right_panel, self)
        bot = right_bot_panel(self.right_panel, self)
        
        right_sizer.Add(top, 10, wx.TOP | wx.LEFT | wx.EXPAND, border=5)
        right_sizer.Add(bot, 2, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER | wx.TOP, border=10)

        self.right_panel.SetSizer(right_sizer)

        sizer.Add(self.left_panel, 4, wx.LEFT | wx.EXPAND)
        sizer.Add(self.right_panel, 1, wx.RIGHT | wx.EXPAND)

        self.init_plot()

        # Plot the polylines:
        i = 0
        for pl in self.controller.calc_graph():
            self.plot(pl, c=self.controller.lines_colors[i])
            i += 1

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()
        self.Center()
        
        # Callbacks
        self.Bind(wx.EVT_CLOSE, self.controller.on_close)

    def init_plot(self, num_values=10.0, height=255.0):
        """
        Initializes the Density Chart/Plot, setting the axes size to
          WIDTH: 0 - number of values being plotted
          HEIGHT: 0 - 255 (or whatever scale the numbers are represented by) 256-bit in CXV's case
        """
        self.figure = Figure()
        self.canvas = FigureCanvasWxAgg(self.left_panel, -1, self.figure)
        self.canvas.SetBackgroundColour('grey')
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)
        self.axes.set_title("Density Values per Polyline")
        self.axes.set_xlabel("Polyline Position (0: Beginning, n: End)")
        self.axes.set_ylabel("Equivalent Aluminum Thickness (g/cm"+u'\u00B3'+")")
        max_val = float(self.controller.dicom_controller.calibrate_controller.max_thickness)
        min_val = float(self.controller.dicom_controller.calibrate_controller.min_thickness)
        self.axes.set_ylim([min_val, max_val])
        toolbar = NavigationToolbar(self.canvas)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.GROW)
        self.sizer.Add(toolbar)
        self.left_panel.SetSizer(self.sizer)
        
    def plot(self, arr, c):
        self.axes.plot(arr, color=c)

class right_top_panel(sp.ScrolledPanel, View):
    def __init__(self, parent, view):
        sp.ScrolledPanel.__init__(self, parent, id=wx.ID_ANY)
        self.view = view
        sizer = wx.FlexGridSizer(0, 1, 3, 3) # Rows, Columns, H-Gap, V-Gap

        header = wx.StaticText(self, -1, "Polylines:")
        sizer.Add(header)

        for polyline in self.view.controller.dicom_controller.polyline_controller.polylines:
            name = polyline.label.get_text()
            self.view.controller.lines_names.append(name)
            checkbox = wx.CheckBox(self, -1, name)
            checkbox.SetValue(True)
            self.Bind(wx.EVT_CHECKBOX, self.on_checkbox)
            sizer.Add(checkbox)

        self.unit = 20
        width, height = self.GetSizeTuple()
        self.SetScrollbars(self.unit, self.unit, width/self.unit, height/self.unit, 0, 0)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.FitInside()
        self.Fit()
        self.SetupScrolling()
    
    def on_checkbox(self, event):
        # Get the polyline name that is being removed/re-added
        name = event.GetEventObject().GetLabelText()
        if len(name) == 2: # one number (0 - 9)
            name = name[1]
        elif len(name) == 3: # two numbers (0 - 99)
            name = str(name[1] + name[2])
        elif len(name) == 4: # three numbers (0 - 999)
            name = str(name[1] + name[2] + name[3])
        elif len(name) == 5: # four numbers (0 - 9999)
            name = str(name[1] + name[2] + name[3] + name[4])

        # clear canvas
        self.view.axes.clear()

        if (event.IsChecked()): # Re-add
            for line in self.view.controller.all_lines:
                if line[0] == ("t" + str(name)):
                    line[3] = True
        else: # Remove
            for line in self.view.controller.all_lines:
                if line[0] == ("t" + str(name)):
                    line[3] = False

        # Re-plot lines
        for line in self.view.controller.all_lines:
            if line[3] == True:
                self.view.plot(line[1], c=line[2])

        # Reset grid and axes
        self.view.axes.grid(True)
        self.view.axes.set_title("Density Values per Polyline")
        self.view.axes.set_xlabel("Polyline Position (0: Beginning, n: End)")
        self.view.axes.set_ylabel("Equivalent Aluminum Thickness (g/cm"+u'\u00B3'+")")
        max_val = float(self.view.controller.dicom_controller.calibrate_controller.max_thickness)
        min_val = float(self.view.controller.dicom_controller.calibrate_controller.min_thickness)
        self.view.axes.set_ylim([min_val, max_val])

        # Redraw canvas
        self.view.canvas.draw()

class right_bot_panel(wx.Panel, View):
    def __init__(self, parent, view):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)
        self.view = view

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Export image button
        button = wx.Button(self, id=wx.ID_ANY, label="Export Image")
        button.Bind(wx.EVT_BUTTON, self.on_image)
        sizer.Add(button, 1, wx.GROW)
        
        # Export data button
        button = wx.Button(self, id=wx.ID_ANY, label="Export Data")
        button.Bind(wx.EVT_BUTTON, self.on_graph)
        sizer.Add(button, 1, wx.GROW)

        self.SetSizer(sizer)

    def on_image(self, event):
        self.view.controller.on_export_image(event)
        
    def on_graph(self, event):
        self.view.controller.on_export_graph(event)