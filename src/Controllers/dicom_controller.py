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
from Controllers import calibrate_controller
from Controllers import contrast_controller
from Controllers import coral_controller
from Controllers import image_info_controller
from Controllers import overlay_controller
from Controllers import overview_controller
from Controllers import polyline_controller
from Controllers import xml_controller
from Controllers import zoom_controller
from Models import dicom_model
from lib import browse_dialog
from lib import progress_bar
from lib import save_session
from Views import dicom_view
import getpass
import wx
import re
import os
import math

class Controller():
    
    def __init__(self):
        self.model = dicom_model.Model()
        self.ptr = None
        self.aspect_patt = re.compile('\d+')
        self.ztf_patt = re.compile('Zoom to fit')
        self.ztf = True
        self.zoom = False # Zoom tool from toolbar
        self.coral = False
        self.coral_locked = False
        self.polyline = False
        self.polyline_locked = False
        self.calib = False
        self.coral_controller = None
        self.overlay_controller = None
        self.polyline_controller = None
        self.calibrate_controller = None
        self.zoom_controller = None
        self.save_session = None
        self.changed = False
        self.pan_image = False # Is the user able to currently pan the image?
        self.left_down = False # Is the user holding the left mouse button?
        self.view = dicom_view.View(self, self.model)
        self.background = None
        self.xml = None
        self.drag = False
        self.plugin_directory = ""

        # Check for the XML config file. If it's installed,
        # read the corresponding data. If it's not installed,
        # install it to the user's home directory, setting
        # default values.
        path = os.path.expanduser('~')
        if os.path.exists(r'' + path + '\.cxvrc.xml'):
            self.xml = xml_controller.Controller(path + '\.cxvrc.xml')
            self.xml.load_file()
            self.plugin_directory = self.xml.get_plugin_directory()
        else:
            self.xml = xml_controller.Controller(path + '\.cxvrc.xml')
            self.xml.create_config()

    def on_open(self, event):
        dialog = wx.FileDialog(None, wildcard='DICOM (*.DCM)|*.DCM|Saved Session (*.txt)|*.txt', style=wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            new = True
            if self.model.image_array is not None:  # opening a project on top of another
                self.save_prompt()
                self.close_current()
                new = False
            path = dialog.GetPath()
            if (path[-4:] == '.dcm') or (path[-4:] == '.DCM'):
                self.open_dicom_file(path, new)
            else:
                self.open_saved_session(path, new)
            self.view.aspect_cb.Enable()
            tools = ['&Save...\tCtrl+S',
                     'Image Overview', 'Image Information', 
                     'Zoom In', 'Zoom Out', 'Adjust Contrast', 
                     'Adjust Coral Slab', 'Draw Polylines',
                     'Adjust Calibration Region']
            self.enable_tools(tools, True)

    def open_dicom_file(self, path, new):
        p = path.split(os.sep)
        p = p[:3] + p[-2:]
        p[2] = '...'
        label = 'Loading '
        for each in p:
            label += (each + os.sep)
        label = label[:-1]
        pb = progress_bar.ProgressBar('Loading DICOM', label, 7, self.view)
        self.model.image_array = self.model.load_dicom_image(path)
        pb.update(label)
        y, x = self.model.get_image_shape()
        pb.update(label)
        try: rgba, self.ptr = self.model.allocate_array((y, x, 4))
        except ValueError: rgba, self.ptr = self.model.allocate_array((y, x, 4))
        pb.update(label)
        self.model.image_array = self.model.normalize_intensity(self.model.image_array)
        pb.update(label)
        self.model.image_array = self.model.invert_grayscale(self.model.image_array)
        pb.update(label)
        self.model.image_array = self.model.set_display_data(rgba, self.model.image_array, 1.0)
        pb.update(label)
        self.view.init_plot(new)
        pb.finish(label)
        self.cleanup()
    
    def open_saved_session(self, path, new):
        self.save_session = save_session.SaveSession(self, path)
        self.save_session.read()
        self.open_dicom_file(self.save_session.fn, new)
        self.save_session.load()
           
    def close_current(self):
        self.model.deallocate_array(self.ptr)
        self.view.figure.delaxes(self.view.axes)
        self.coral_controller = None
        self.overlay_controller = None
        self.polyline_controller = None
        self.save_session = None
        self.changed = False
        self.enable_tools(['Lock Coral Slab', 'Filtered Overlays'], False)
        
    def on_quit(self, event):
        self.save_prompt()
        wx.Exit()
        
    def save_prompt(self):
        if self.save_session and self.changed:
            msg = 'The contents of ' + self.save_session.path.split(os.sep)[-1] + \
            ' has changed.\n\n Do you want to save the changes?'
            dialog = wx.MessageDialog(self.view, msg, 'CXV', style=wx.YES_NO|wx.CANCEL)
            choice = dialog.ShowModal()
            if choice==wx.ID_CANCEL:
                return
            elif choice==wx.ID_YES:
                self.save_session.write()
                
    def enable_tools(self, tools, enable):
        for tool in tools:
            self.view.toolbar.EnableTool(self.view.toolbar_ids[tool], enable)
            self.view.menubar.FindItemById(self.view.menubar_ids[tool]).Enable(enable)

    def pan_view(self, x, y):
        """
        Pans the user's scrollpane in the direction that they're moving their mouse.
        
        @var x: the x position that the mouse has moved to
        @var y: the y position that the mouse has moved to
        """
        # Get the current position of the scrollbars
        init_pos_x, init_pos_y = self.view.scroll.GetViewStart()

        # Find the direction that the user is dragging their mouse
        # Negative = Scrolling: DOWN or LEFT, Dragging: UP or RIGHT
        # Positive = Scrolling: UP or RIGHT, Dragging: DOWN or LEFT
        x_delta = self.previous_x - x
        y_delta = self.previous_y - y

        # Increase or decrease the scrollbars depending on which
        # direction the user is dragging their mouse
        if (x_delta > 0): # Left
            init_pos_x += 1
        elif (x_delta < 0): # Right
            init_pos_x -= 1
        if (y_delta > 0): # Down
            init_pos_y += 1
        elif (y_delta < 0): # Up
            init_pos_y -= 1

        # Update the scrollbar with the new position
        self.view.scroll.Scroll(init_pos_x, init_pos_y)

    def resize_image(self, b=True, sx=0, sy=0):
        self.resize_mpl_widgets()
        # Ordering here determines a couple things:
        # if self.cleanup() happens first, we see (0,0) in scrollbar,
        # then it scrolls to the desired position
        #
        # if self.set_scrollbars() happens first, it scrolls first but
        # we get an ugly overlapping image until the canvas refreshes
        self.set_scrollbars(b, sx, sy)
        self.cache_background()
        self.cleanup()
        self.update_overview()
        
    def resize_mpl_widgets(self):
        y, x = self.model.get_image_shape()
        self.view.canvas.resize(x*self.view.aspect, y*self.view.aspect)  # canvas gets set in pixels
        self.view.figure.set_size_inches((x*self.view.aspect)/72.0, (y*self.view.aspect)/72.0)  # figure gets set in inches
        
    def set_scrollbars(self, b=True, sx=0, sy=0):
        """ b is used here because unless we're drag zooming in, the 
        Scroll method has to be executed before setting the scrollbars.
        
        Order of execution matters for some reason, otherwise we get a
        blank gray screen?
        """
        y, x = self.model.get_image_shape()
        if b: # Scroll here
            self.view.scroll.Scroll(sx, sy)
        scroll_unit = self.view.aspect*100.0
        self.su = scroll_unit
        try:
            self.view.scroll.SetScrollbars(scroll_unit, scroll_unit, 
                                           (x*self.view.aspect)/scroll_unit, 
                                           (y*self.view.aspect)/scroll_unit)
        except ZeroDivisionError:
            pass
        self.view.scroll.Refresh()
        if not b: # Or scroll here (drag zooming uses this)
            self.view.scroll.Scroll(sx, sy)
        
    def cache_background(self):
        self.view.canvas.draw() # cache clean slate background
        self.background = self.view.canvas.copy_from_bbox(self.view.axes.bbox)
        self.draw_all()
        
    def draw_all(self, bool=True):
        if bool:
            self.view.canvas.restore_region(self.background)
        if self.coral_controller:
            print 'Draw rect'
            self.coral_controller.draw_rect(self.coral, self.coral_locked)
        if self.polyline_controller:
            self.polyline_controller.draw_polylines(self.polyline, self.polyline_locked)
        if self.calibrate_controller:
            self.calibrate_controller.draw_rect(self.calib, False)
        if bool:
            self.view.canvas.blit(self.view.axes.bbox)
        
    def cleanup(self, event=None):
        try:    # ignore first couple calls before canvas instantiation
            if event:
                if wx.FindWindowById(event.GetId()) != self.view:
                    x, y = wx.FindWindowById(event.GetId()).GetPositionTuple()
                    w, h = wx.FindWindowById(event.GetId()).GetSizeTuple()
                    X, Y = self.view.GetPositionTuple()
                    W, H = self.view.GetSizeTuple()
                    if (x > X+W) or (y > Y+H):
                        return
                    if (x+w < X) or (y+h < Y):
                        return
            x, y = self.view.canvas.get_width_height()
            X, Y = self.view.scroll.GetSizeTuple()
            if (X > x) or (Y > y):
                self.view.canvas.ClearBackground()
                self.view.canvas.Refresh(eraseBackground=True)
        except:
            pass

    """Events and Tool handlers"""
    def on_overview(self, event):
        try: self.overview_controller.view.Raise()
        except AttributeError: self.overview_controller = overview_controller.Controller(self.model, self.view)
        
    def update_overview(self):
        try: self.overview_controller.update_viewable_area()
        except AttributeError: pass

    def on_show_popup(self, event):
        if not self.ztf and not self.zoom:
            self.popup_menu = wx.Menu()
            self.popup_menu.Append(-1, 'Zoom to fit')

            # Better to set this event here when we need it because if it's set in
            # the view class, all menu items will fire this event.
            self.view.Bind(wx.EVT_MENU, self.on_popup_item_selected)
            x, y = wx.GetMousePosition()
            y -= 35 # Ugly but GetMousePosition returns y position too low
            pos = x, y
            self.view.PopupMenu(self.popup_menu, pos)

            # Unbind the event, otherwise we get a screen flickering if the user opens
            # multiple popupmenu's without selecting an item. This is caused because
            # there would now be multiple events open and waiting for input. Once input
            # is given, all those events are fired at once, resizing our screen multiple
            # times.
            self.view.Unbind(wx.EVT_MENU)
            self.popup_menu.Destroy()

    def on_popup_item_selected(self, event):
        self.ztf = True
        self.on_resize(event)
        self.view.canvas.Refresh()

    def on_mouse_motion(self, event):
        if self.pan_image and self.left_down:
            aspect = (self.view.aspect*100.0)
            try:
                x = int(event.xdata)
                y = int(event.ydata)
            except TypeError: 
                # This is thrown if the user clicks just barely
                # outside of the image bounds (a few pixels at most),
                # when the coordinates show (x, y) in the status bar.
                return

            total_x = math.fabs(x - self.previous_x) # total x plane mouse movement
            total_y = math.fabs(y - self.previous_y) # total y plane mouse movement

            # Force the method to only run if the user has moved their mouse
            # more than 'aspect' number of pixels. This ensures that the mouse
            # moves relative to the scroll units of the scrollbar.
            if (total_x > aspect or total_y > aspect):
                if (total_x < aspect):
                    self.pan_view(self.previous_x, y)
                elif (total_y < aspect):
                    self.pan_view(x, self.previous_y)
                else:
                    self.pan_view(x, y)
                self.view.canvas.Refresh(eraseBackground=False)

        if event.inaxes == self.view.axes:
            try:
                self.view.statusbar.SetStatusText("Pixel Position: (%i, %i)" % (event.xdata, event.ydata), 0)
                self.view.statusbar.SetStatusText("Pixel Intensity: %.4f" % self.model.image_array[event.ydata][event.xdata][0], 1)
            except:
                self.view.statusbar.SetStatusText("Pixel Position: (x, y)", 0)
                self.view.statusbar.SetStatusText("Pixel Intensity", 1)

        elif event.inaxes == self.view.ov_axes: # check if mouse is in the overlay axes
            x = event.xdata + self.coral_slab[0]
            y = event.ydata + self.coral_slab[1]
            self.view.statusbar.SetStatusText("Pixel Position: (%i, %i)" % (x, y), 0)
            self.view.statusbar.SetStatusText("Pixel Intensity: %.4f" % self.overlay_controller.overlay[event.ydata][event.xdata], 1)

        if not self.pan_image and not self.zoom:
            if self.polyline:
                self.polyline_controller.on_mouse_motion(event)
            elif self.coral:
                self.coral_controller.on_mouse_motion(event)
            elif self.calib:
                self.calibrate_controller.on_mouse_motion(event)

        # TODO: this
        if self.drag:
            self.draw_all()
        else:
            self.draw_all(False)
        self.view.canvas.Refresh(eraseBackground=False)

    def on_mouse_press(self, event):
        if event.button == 1: # Left mouse button
            self.left_down = True
            self.drag = True
            # Set the prev_x and prev_y to the mouse click position
            try:
                self.previous_x = int(event.xdata)
                self.previous_y = int(event.ydata)
            except TypeError:
                # This is thrown if the user clicks just barely
                # outside of the image bounds (a few pixels at most),
                # when the coordinates show (x, y) in the status bar.
                pass
        elif event.button == 2: # Scroll-wheel button??
            return
        elif event.button == 3: # Right mouse button
            pass

        if not self.pan_image:
            if self.polyline:
                self.polyline_controller.on_mouse_press(event)
            elif self.coral:
                self.coral_controller.on_mouse_press(event)
            elif self.calib:
                self.calibrate_controller.on_mouse_press(event)
            self.draw_all()

    def on_mouse_release(self, event):
        self.left_down = False
        self.drag = False
        if not self.pan_image:
            if self.polyline:
                self.polyline_controller.on_mouse_release(event)
            elif self.coral:
                self.coral_slab = self.coral_controller.on_mouse_release(event)
            elif self.calib:
                self.calib_region = self.calibrate_controller.on_mouse_release(event)
            self.draw_all()

    def on_key_press(self, event):
        if event.key == ' ' and not self.zoom: # Is the user pressing the SPACE BAR?
            self.pan_image = True
            self.view.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        elif event.key == 'd': # DEBUG
            print 'DEBUG'

    def on_key_release(self, event):
        self.pan_image = False
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

    def on_figure_leave(self, event):
        self.view.statusbar.SetStatusText("Pixel Position: (x, y)", 0)
        self.view.statusbar.SetStatusText("Pixel Intensity", 1)

    def on_scroll(self, event):
        event.Skip()
        self.update_overview()

    def on_resize(self, event):
        event.Skip()
        if self.ztf:
            try:    # ignore first few events before controller instantiation
                y, = self.view.scroll.GetSizeTuple()[-1:]
                iHt, = self.model.get_image_shape()[:-1]
                self.view.aspect = (float(y)/float(iHt))
                self.resize_image()
                self.view.aspect_cb.SetValue('Zoom to fit')
            except AttributeError: 
                pass
        else:
            self.cleanup()
        self.update_overview()

    def on_aspect(self, event):
        m = self.ztf_patt.match(self.view.aspect_cb.GetLabel()) # zoom to fit
        if m: 
            self.ztf = True
            self.on_resize(event)
        else: self.ztf = False
            
        m = self.aspect_patt.match(self.view.aspect_cb.GetLabel())  # percent
        if not m: self.view.aspect_cb.SetValue(str(int(self.view.aspect*100.0))+'%')
        else:
            if int(m.group(0)) > 120:
                self.view.aspect = 1.20
                self.view.aspect_cb.SetValue('120%')
            elif int(m.group(0)) < 10:
                self.view.aspect = 0.1
                self.view.aspect_cb.SetValue('10%')
            else:
                aspect = float(m.group(0))/100.0
                self.view.aspect = aspect
                self.view.aspect_cb.SetValue(str(int(m.group(0)))+'%')
        self.view.canvas.SetFocus() # Sets focus back to the canvas, otherwise combobox still has keyboard focus
        self.resize_image()

    def on_image_info(self, event):
        try: self.image_info_controller.view.Raise()
        except AttributeError: self.image_info_controller = image_info_controller.Controller(self, self.model)

    def on_coral(self, event):
        self.coral = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Coral Slab'])
        if self.coral_locked:
            self.enable_tools(['Filtered Overlays'], False)
        self.coral_locked = False
        self.polyline = False
        self.calib = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        if not self.coral_controller:   # first open
            self.coral_controller = coral_controller.Controller(self.view, self.background)
            self.enable_tools(['Lock Coral Slab'], True)
        else:
            try:    # remove overlay if already added
                self.view.figure.delaxes(self.view.ov_axes)
                self.overlay_controller.view.Destroy()
                del self.overlay_controller
                self.overlay_controller = None
                self.cache_background()
            except:
                pass
        self.draw_all()

    def on_lock_coral(self, event, show=True):
        if self.coral_locked: return  # already locked
        self.coral = False
        self.coral_locked = True
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Coral Slab'], False)
        self.enable_tools(['Filtered Overlays'], True)
        if not self.overlay_controller:
            self.overlay_controller = overlay_controller.Controller(self.view, self, self.model, self.background, show)
        self.draw_all()
        self.overlay_controller.create_overlays()
        self.cleanup()

    def on_contrast(self, event):
        try: self.contrast_controller.view.Raise()
        except AttributeError: self.contrast_controller = contrast_controller.Controller(self.view, self.model)
        
    def on_overlay(self, event):
        if not self.coral_locked:
            self.on_lock_coral(event, True) # have worker thread add and display overlay
        elif not self.overlay_controller.view.IsShown():    # first press
            self.overlay_controller.display()
            self.overlay_controller.view.Show()
        elif self.overlay_controller.view.IsShown():
            self.overlay_controller.view.Raise()

    def on_plugin(self, event):
        pass

    def on_polyline(self, event):
        self.polyline = self.view.toolbar.GetToolState(self.view.toolbar_ids['Draw Polylines'])
        self.polyline_locked = False
        self.coral = False
        self.calib = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Coral Slab'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        if not self.polyline_controller:
            self.polyline_controller = polyline_controller.Controller(self, self.view, self.background)
            #self.enable_tools(['Lock Polylines'], True)
        self.draw_all()
        
    def on_lock_polyline(self, event):
        self.polyline = False
        self.polyline_locked = True
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        self.draw_all()
        
    def on_calibrate(self, event):
        self.calib = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Calibration Region'])
        self.coral = False
        self.polyline = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Coral Slab'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        if not self.calibrate_controller:
            self.calibrate_controller = calibrate_controller.Controller(self.view, self.background)
            self.enable_tools(['Set Density Parameters'], True)
        self.draw_all()
            
    def on_density_params(self, event):
        self.calib = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        self.calibrate_controller.on_density_params(event)
        self.draw_all()
        
    def on_save(self, event):
        if not self.save_session:
            dialog = wx.FileDialog(self.view, "Save As", style=wx.SAVE|wx.OVERWRITE_PROMPT, wildcard='Text File (*.txt)|*.txt')
            dialog.SetFilename(self.model.get_image_name().split('.')[0]+'.txt')
            if dialog.ShowModal()==wx.ID_OK:
                self.save_session = save_session.SaveSession(self, dialog.GetPath())
                self.save_session.write()
        else:
            self.save_session.write()
    
    def on_plugin_properties(self, event=None):
        browse = browse_dialog.BrowseDialog(None, title='Default Plugin Directory')
        browse.ShowModal()
        browse.Destroy()

        # Update the view to show the changes in the menu
        self.view.create_menubar()

    def on_browse_callback(self, event):
        pass

    def on_about_filter(self, event, plugin):
        """ Shows a wx.AboutDialog for the plugin that has been
        clicked in the Tools --> Filter Plugins --> menu item. Limits
        the words per line to 10. Ugly work around, but since we
        can't have multiple lines in the .plugin file for the Description
        we need to handle that here.
        """
        description = plugin.description
        span = 10
        words = description.split(" ")
        list = [" ".join(words[i:i+span]) for i in range(0, len(words), span)]
        description = '\n'.join(list)

        info = wx.AboutDialogInfo()
        info.SetName(plugin.name)
        info.SetVersion(plugin.version)
        info.SetDescription(description)
        info.SetWebSite(plugin.website)
        info.AddDeveloper(plugin.author)

        wx.AboutBox(info)

    def on_help(self, event):
        pass

    def on_about(self, event):
        description = "Coral X-Ray Viewer does... INFO ABOUT CXV HERE"

        info = wx.AboutDialogInfo()
        info.SetName('Coral X-Ray Viewer')
        info.SetVersion('1.00')
        info.SetDescription(description)
        info.SetCopyright('(C) 2010 - 2012 US Geological Survey, DOI')
        info.SetWebSite('www.usgs.gov')
        info.AddDeveloper('Luke Mueller')
        info.AddDeveloper('Adam Childs')

        wx.AboutBox(info)