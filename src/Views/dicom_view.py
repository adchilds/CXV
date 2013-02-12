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
from Controllers import xml_controller
from Controllers import zoom_controller
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.widgets import RectangleSelector
import matplotlib.transforms as transforms
from yapsy.PluginManager import PluginManager
import imp
import os
import sys
import wx

class View(wx.Frame):

    def __init__(self, controller, model):
        self.controller = controller
        self.model = model
        self.zoom_controller = zoom_controller.Controller(controller, self, model)
        self.aspect = 1.0
        self.toolbar_ids = {}
        self.menubar_ids = {}
        self.connect_ids = []
        self.ov_axes = ''
        self.toggle_selector = None
        self.figure = None

        wx.Frame.__init__(self,
                          parent=None,
                          title="Coral X-Ray Viewer",
                          size=(850, 750),
                          pos=(0,0))
        self.SetMinSize((100, 100))

        self.scroll = wx.ScrolledWindow(self, -1)
        self.scroll.SetBackgroundColour('grey')    
        
        self.create_menubar()
        self.create_toolbar()
        self.create_statusbar()

        self.scroll.Bind(wx.EVT_SCROLLWIN, self.controller.on_scroll) # scroll event
        self.scroll.Bind(wx.EVT_SCROLL, self.on_scroll)
        self.Bind(wx.EVT_SIZE, self.controller.on_resize)
        self.Bind(wx.EVT_ACTIVATE, self.controller.cleanup)
        self.Bind(wx.EVT_CLOSE, self.controller.on_quit)
        self.Bind(wx.EVT_CONTEXT_MENU, self.controller.on_show_popup)

        self.Show()

    def on_scroll(self, event):
        event.Skip()
        self.controller.state_changed(True)

    def create_menubar(self):
        self.menubar = wx.MenuBar()
        for name in self.menu_names():
            menu = wx.Menu()
            for each in self.menu_options()[self.menu_names().index(name)]:
                self.add_menu_option(menu, *each)
            self.menubar.Append(menu, name)
        self.SetMenuBar(self.menubar)
        
    def add_menu_option(self, menu, label, accel, handler, enabled, has_submenu, submenu):
        if not label:
            menu.AppendSeparator()
        else:
            menu_id = wx.NewId()
            self.menubar_ids[label] = menu_id
            if has_submenu:
                if label == 'Filter Plugins':
                    option = menu.AppendMenu(menu_id, label, self.plugin_submenu())
                else:
                    option = menu.AppendMenu(menu_id, label, submenu)
            else:
                option = menu.Append(menu_id, label)
            option.Enable(enabled)
            if accel:
                wx.AcceleratorTable([ (accel[0], ord(accel[1]), option.GetId()) ])
            self.Bind(wx.EVT_MENU, handler, option)
        
    def menu_names(self):
        return ('File', 'Tools', 'Help')
    
    def menu_options(self):
        """ ('TEXT', (ACCELERATOR), HANDLER, ENABLED, HAS_SUBMENU, SUBMENU METHOD """
        return ( [ # File
                  ('&Open...\tCtrl+O', (wx.ACCEL_CTRL, 'O'), self.controller.on_open, True, False, None),
                  ('&Save\tCtrl+S', (wx.ACCEL_CTRL, 'S'), self.controller.on_save, False, False, None),
                  ('Save As...', (), self.controller.on_save_as, False, False, None),
                  ('', '', '', True, False, None),
                  ('Export', (), self.controller.on_export, False, False, None),
                  ('', '', '', True, False, None),
                  ('&Quit\tCtrl+Q', (wx.ACCEL_CTRL, 'Q'), self.controller.on_quit, True, False, None)
                  ],
                 [ # Tools
                  ('Image Overview', (), self.controller.on_overview, False, False, None),
                  ('Image Information', (), self.controller.on_image_info, False, False, None),
                  ('', '', '', True, False, None),
#                  ('Rotate Image', (), self.controller.on_rotate_image, False, False, None), 
                  ('Pan Image', (), self.controller.on_pan_image_menu, False, False, None),
                  ('Rotate Image', (), self.controller.on_rotate, False, False, None),
                  ('Zoom In', (), self.zoom_controller.on_zoom_in_menu, False, False, None),
                  ('Zoom Out', (), self.zoom_controller.on_zoom_out, False, False, None),
                  ('', '', '', True, False, None),
#                  ('Adjust Contrast', (), self.controller.on_contrast, False, False, None),
#                  ('', '', '', True, False, None),
                  ('Adjust Target Area', (), self.controller.on_coral_menu, False, False, None),
                  ('', '', '', True, False, None),
                  ('Filtered Overlays', (), self.controller.on_overlay, False, False, None),
                  ('Filter Plugins', (), self.controller.on_plugin, True, True, None),
                  ('', '', '', True, False, None),
                  ('Adjust Calibration Region', (), self.controller.on_calibrate_menu, False, False, None),
                  ('Set Calibration Parameters', (), self.controller.on_density_params, False, False, None),
                  ('', '', '', True, False, None),
                  ('Draw Polylines', (), self.controller.on_polyline_menu, False, False, None),
                  ],
                 [ # Help
                  ('Help', (), self.controller.on_help, True, False, None),
                  ('About', (), self.controller.on_about, True, False, None)
                  ]
                )

    def plugin_submenu(self):
        """ Creates the plugin submenu in the menubar which displays all plugins
        and allows the user to specify a secondary plugin directory.
        """
        menu = wx.Menu()

        """
        # Add a plugin from another directory to the default directory
        addPlugin = wx.MenuItem(menu, wx.ID_ANY, 'Add Plugin')
        menu.AppendItem(addPlugin)
        self.Bind(wx.EVT_MENU, self.controller.on_add_plugin, addPlugin)
        """

        # Set directory where extra plugins are held
        props = wx.MenuItem(menu, wx.ID_ANY, 'Set Directory')
        menu.AppendItem(props)
        self.Bind(wx.EVT_MENU, self.controller.on_plugin_properties, props)

        menu.AppendSeparator()

        # Get the default plugin directory, using XML
        path = os.path.expanduser('~')
        xml = xml_controller.Controller(path + '\.cxvrc.xml')
        xml.load_file()

        if os.path.exists(os.path.expanduser('~') + os.sep + "plugins"):
            default_dir = os.path.expanduser('~') + os.sep + "plugins"
        else:
            default_dir = self.get_main_dir() + os.sep + "plugins"

        if xml.get_plugin_directory() == "" or xml.get_plugin_directory() is None:
            directory = [default_dir]
        else:
            directory = [default_dir, xml.get_plugin_directory()]

        # Load the plugins from the specified plugin directory/s.
        manager = PluginManager()
        manager.setPluginPlaces(directory)
        manager.setPluginInfoExtension('plugin')
        manager.collectPlugins()

        for plugin in manager.getAllPlugins():
            item = wx.MenuItem(menu, wx.ID_ANY, plugin.name)
            menu.AppendItem(item)
            self.better_bind(wx.EVT_MENU, item, self.controller.on_about_filter, plugin)

        return menu

    def better_bind(self, evt_type, instance, handler, *args, **kwargs):
        self.Bind(evt_type, lambda event: handler(event, *args, **kwargs), instance)

    def create_toolbar(self):
        self.toolbar = self.CreateToolBar()
        for each in self.toolbar_data():
            self.add_tool(self.toolbar, *each)
        self.toolbar.Realize()
    
    def add_tool(self, toolbar, tool_type, label, bmp, handler, enabled):
        if tool_type == 'separator':
            toolbar.AddSeparator()
        elif tool_type == 'control':
            toolbar.AddControl(label)
        else:
            bmp = wx.Image(self.get_main_dir() + os.sep + bmp, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            tool_id = wx.NewId()
            self.toolbar_ids[label] = tool_id
            if tool_type == 'toggle':
                tool = toolbar.AddCheckTool(tool_id, bmp, wx.NullBitmap, label, '')
            elif tool_type == 'simple':
                tool = toolbar.AddSimpleTool(tool_id, bmp, label, '')
            toolbar.EnableTool(tool_id, enabled)
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
                ('simple', '&Open...\tCtrl+O', 'images' + os.sep + 'open.png', self.controller.on_open, True),
                ('simple', '&Save\tCtrl+S', 'images' + os.sep + 'save.png', self.controller.on_save, False),
                ('separator', '', '', '', ''),
                ('simple', 'Image Overview', 'images' + os.sep + 'overview.png', self.controller.on_overview, False),
                ('simple', 'Image Information', 'images' + os.sep + 'info.png', self.controller.on_image_info, False),
                ('separator', '', '', '', ''),
#                ('simple', 'Rotate Image', 'images' + os.sep + 'rotate_counter-clock.png', self.controller.on_rotate_image, False),
                ('toggle', 'Pan Image', 'images' + os.sep + 'cursor_hand.png', self.controller.on_pan_image, False),
                ('simple', 'Rotate Image', 'images' + os.sep + 'rotate_image.png', self.controller.on_rotate, False),
                ('toggle', 'Zoom In', 'images' + os.sep + 'zoom_in_toolbar.png', self.zoom_controller.on_zoom_in, False),
                ('simple', 'Zoom Out', 'images' + os.sep + 'zoom_out_toolbar.png', self.zoom_controller.on_zoom_out, False),
                ('control', self.aspect_cb, '', '', ''),
                ('separator', '', '', '', ''),
#                ('simple', 'Adjust Contrast', 'images' + os.sep + 'contrast.png', self.controller.on_contrast, False),
#                ('separator', '', '', '', ''),
                ('toggle', 'Adjust Target Area', 'images' + os.sep + 'coral.png', self.controller.on_coral, False),
#                ('simple', 'Lock Target Area', 'images' + os.sep + 'lock_coral.png', self.controller.on_lock_coral, False),
#                ('separator', '', '', '', ''),
                ('simple', 'Filtered Overlays', 'images' + os.sep + 'overlay.png', self.controller.on_overlay, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Adjust Calibration Region', 'images' + os.sep + 'calibrate.png', self.controller.on_calibrate, False),
                ('toggle', 'Set Calibration Parameters', 'images' + os.sep + 'density.png', self.controller.on_density_params, False),
                ('separator', '', '', '', ''),
                ('toggle', 'Draw Polylines', 'images' + os.sep + 'polyline.png', self.controller.on_polyline, False),
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
            self.figure = Figure(figsize=(x*2/72.0, y*2/72.0), dpi=72)
            self.canvas = FigureCanvasWxAgg(self.scroll, -1, self.figure)
            self.canvas.SetBackgroundColour('grey')
        self.axes = self.figure.add_axes([0.0, 0.0, 1.0, 1.0])
        self.axes.set_axis_off()
        self.axes.imshow(self.model.get_image(), aspect='auto') # aspect='auto' sets image aspect to match the size of axes
        self.axes.set_autoscale_on(False)   # do not apply autoscaling on plot commands - VERY IMPORTANT!
        self.mpl_bindings()
        y, = self.scroll.GetSizeTuple()[-1:]
        iHt, = self.model.get_image_shape()[:-1]
        self.aspect = (float(y)/float(iHt))
        self.controller.resize_image()

        # Set the RectangleSelector so that the user can drag zoom when enabled
        rectprops = dict(facecolor='white', edgecolor = 'white', alpha=0.25, fill=True)
        self.toggle_selector = RectangleSelector(self.axes,
                                        self.zoom_controller.on_zoom,
                                        drawtype='box',
                                        useblit=True,
                                        rectprops=rectprops,
                                        button=[1], # Left mouse button
                                        minspanx=1, minspany=1,
                                        spancoords='data')
        self.toggle_selector.set_active(False)
        
    def main_is_frozen(self):
        return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") or # old py2exe
            imp.is_frozen("__main__")) # tools/freeze
        
    def get_main_dir(self):
        if self.main_is_frozen():
            return os.path.dirname(sys.executable)
        return os.path.dirname(sys.argv[0])