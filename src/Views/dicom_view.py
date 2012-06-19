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
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.widgets import RectangleSelector
import wx

class View(wx.Frame):

    def __init__(self, controller, model):
        self.controller = controller
        self.model = model
        self.aspect = 1.0
        self.toolbar_ids = {}
        self.menubar_ids = {}
        self.connect_ids = []
        self.ov_axes = ''
        self.toggle_selector = None

        wx.Frame.__init__(self,
                          parent=None,
                          title="DICOM Viewer",
                          size=(850, 750),
                          pos=(0,0))

        self.scroll = wx.ScrolledWindow(self, -1)
        self.scroll.SetBackgroundColour('grey')    
        
        self.create_menubar()
        self.create_toolbar()
        self.create_statusbar()

        self.scroll.Bind(wx.EVT_SCROLLWIN, self.controller.on_scroll) # scroll event
        self.Bind(wx.EVT_SIZE, self.controller.on_resize)
        self.Bind(wx.EVT_ACTIVATE, self.controller.cleanup)
        self.Bind(wx.EVT_CLOSE, self.controller.on_quit)
        self.Bind(wx.EVT_CONTEXT_MENU, self.controller.on_show_popup)

        # Dummy figure/canvas set, so we can set the NavigationToolbar here
        # If we set it when creating the figure/canvas in init_plot(), the
        # NavigationToolbar will flash quickly, but we don't want to see it!
        # We just need it's functionality.
        self.figure = Figure(figsize=(0,0), dpi=72)
        self.canvas = FigureCanvasWxAgg(self.scroll, -1, self.figure)
        self.mpl_toolbar = NavigationToolbar(self.canvas)
        self.mpl_toolbar.Hide()

        self.Show()

    def create_menubar(self):
        self.menubar = wx.MenuBar()
        for name in self.menu_names():
            menu = wx.Menu()
            for each in self.menu_options()[self.menu_names().index(name)]:
                self.add_menu_option(menu, *each)
            self.menubar.Append(menu, name)
        self.SetMenuBar(self.menubar)
        
    def add_menu_option(self, menu, label, accel, handler, enabled):
        if not label:
            menu.AppendSeparator()
        else:
            id = wx.NewId()
            self.menubar_ids[label] = id
            option = menu.Append(id, label)
            option.Enable(enabled)
            if accel:
                wx.AcceleratorTable([ (accel[0], ord(accel[1]), option.GetId()) ])
            self.Bind(wx.EVT_MENU, handler, option)
        
    def menu_names(self):
        return ('File', 'Tools')
    
    def menu_options(self):
        return ( [# File
                  ('&Open...\tCtrl+O', (wx.ACCEL_CTRL, 'O'), self.controller.on_open, True),
                  ('&Save...\tCtrl+S', (wx.ACCEL_CTRL, 'S'), self.controller.on_save, False),
                  ('', '', '', True),
                  ('&Quit\tCtrl+Q', (wx.ACCEL_CTRL, 'Q'), self.controller.on_quit, True)
                  ],
                 [#Tools
                  ('Image Overview', (), self.controller.on_overview, False),
                  ('Image Information', (), self.controller.on_image_info, False),
                  ('', '', '', True),
                  ('Zoom In', (), self.controller.on_zoom_in, False),
                  ('Zoom Out', (), self.controller.on_zoom_out, False),
                  ('', '', '', True),
                  ('Adjust Contrast', (), self.controller.on_contrast, False),
                  ('', '', '', True),
                  ('Adjust Coral Slab', (), self.controller.on_coral, False),
                  ('Lock Coral Slab', (), self.controller.on_lock_coral, False),
                  ('', '', '', True),
                  ('Overlay Images', (), self.controller.on_overlay, False),
                  ('', '', '', True),
                  ('Adjust Calibration Region', (), self.controller.on_calibrate, False),
                  ('Set Density Parameters', (), self.controller.on_density_params, False),
                  ('', '', '', True),
                  ('Draw Polylines', (), self.controller.on_polyline, False),
                  ('Lock Polylines', (), self.controller.on_lock_polyline, False)
                  ]
                )
               
    def create_toolbar(self):
        self.toolbar = self.CreateToolBar()
        for each in self.toolbar_data():
            self.add_tool(self.toolbar, *each)
        self.toolbar.Realize()
    
    def add_tool(self, toolbar, type, label, bmp, handler, enabled):
        if type == 'separator':
            toolbar.AddSeparator()
        elif type == 'control':
            toolbar.AddControl(label)
        else:
            bmp = wx.Image(bmp).ConvertToBitmap()
            id = wx.NewId()
            self.toolbar_ids[label] = id
            if type == 'toggle':
                tool = toolbar.AddCheckTool(id, bmp, wx.NullBitmap, label, '')
            elif type == 'simple':
                tool = toolbar.AddSimpleTool(id, bmp, label, '')
            toolbar.EnableTool(id, enabled)
            self.Bind(wx.EVT_MENU, handler, tool)
        
    def toolbar_data(self):
        aspects = ['100%', '75%', '50%', '25%', '10%', 'Zoom to fit']
        self.aspect_cb = wx.ComboBox(self.toolbar, -1, '100%',
                                     choices=aspects,
                                     style=wx.CB_DROPDOWN)
        self.aspect_cb.SetValue('Zoom to fit')
        self.Bind(wx.EVT_COMBOBOX, self.controller.on_aspect, self.aspect_cb)
        self.Bind(wx.EVT_TEXT_ENTER, self.controller.on_aspect, self.aspect_cb)
        self.aspect_cb.Disable()
        return (# tool type, description text, icon directory, handler
                ('simple', '&Open...\tCtrl+O', 'images/open.png', self.controller.on_open, True),
                ('simple', '&Save...\tCtrl+S', 'images/save.png', self.controller.on_save, False),
                ('separator', '', '', '', ''),
                ('simple', 'Image Overview', 'images/overview.png', self.controller.on_overview, False),
                ('simple', 'Image Information', 'images/info.png', self.controller.on_image_info, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Zoom In', 'images/zoom_in_toolbar.png', self.controller.on_zoom_in, False),
                ('simple', 'Zoom Out', 'images/zoom_out_toolbar.png', self.controller.on_zoom_out, False),
                ('control', self.aspect_cb, '', '', ''),
                ('separator', '', '', '', ''),
                ('simple', 'Adjust Contrast', 'images/contrast.png', self.controller.on_contrast, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Adjust Coral Slab', 'images/coral.png', self.controller.on_coral, False),
                ('simple', 'Lock Coral Slab', 'images/lock_coral.png', self.controller.on_lock_coral, False),
                ('separator', '', '', '', ''),
                ('simple', 'Overlay Images', 'images/overlay.png', self.controller.on_overlay, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Adjust Calibration Region', 'images/calibrate.png', self.controller.on_calibrate, False),
                ('simple', 'Set Density Parameters', 'images/density.png', self.controller.on_density_params, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Draw Polylines', 'images/polyline.png', self.controller.on_polyline, False),
                ('simple', 'Lock Polylines', 'images/lock_polyline.png', self.controller.on_lock_polyline, False)
               )
        
    def create_statusbar(self):
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-5, -5])
        
    def mpl_bindings(self):
        for each in self.mpl_binds():
            self.connect(*each)
            
    def connect(self, event, handler):
        cid = self.canvas.mpl_connect(event, handler)
        self.connect_ids.append(cid)
        
    def disconnect(self):
        for cid in self.connect_ids:
            self.canvas.mpl_disconnect(cid)
        self.connect_ids = []

    # matplotlib events
    def mpl_binds(self):
        return [
                ('motion_notify_event', self.controller.on_mouse_motion),
                ('figure_leave_event', self.controller.on_figure_leave),
                ('button_press_event', self.controller.on_mouse_press),
                ('button_release_event', self.controller.on_mouse_release),
                ('key_press_event', self.controller.on_key_press),
                ('key_release_event', self.controller.on_key_release)
                ]
        
    def init_plot(self, new):
        if new:
            y, x = self.model.get_image_shape()
            self.figure = Figure(figsize=(x/72.0, y/72.0), dpi=72)
            self.canvas = FigureCanvasWxAgg(self.scroll, -1, self.figure)
            self.canvas.SetBackgroundColour('grey')
        self.axes = self.figure.add_axes([0.0, 0.0, 1.0, 1.0])
        self.axes.set_axis_off()
        self.axes.imshow(self.model.get_image(), aspect='auto') # aspect='auto' sets image aspect to match the size of axes
        self.axes.set_autoscale_on(False)   # do not apply autoscaling on plot commands - VERY IMPORTANT!
        self.axes.set_aspect('equal', 'datalim')
        self.mpl_bindings()
        y, = self.scroll.GetSizeTuple()[-1:]
        iHt, = self.model.get_image_shape()[:-1]
        self.aspect = (float(y)/float(iHt))
        self.controller.resize_image()

        # Set the RectangleSelector so that the user can drag zoom when enabled
        rectprops = dict(facecolor='lightblue', edgecolor = 'lightblue', alpha=0.25, fill=True)
        self.toggle_selector = RectangleSelector(self.axes,
                                        self.line_select_callback,
                                        drawtype='box',
                                        useblit=True,
                                        rectprops=rectprops,
                                        button=[1], # Left mouse button
                                        minspanx=1, minspany=1,
                                        spancoords='pixels')
        self.toggle_selector.set_active(False)

    def line_select_callback(self, click, release):
        'click and release are the press and release events'
        x1, y1 = click.xdata, click.ydata
        x2, y2 = release.xdata, release.ydata
        self.controller.on_drag_zoom([x1, y1, x2, y2])