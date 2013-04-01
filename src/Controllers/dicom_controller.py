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
from Controllers import dxf_controller
from Controllers import image_info_controller
from Controllers import overlay_controller
from Controllers import overview_controller
from Controllers import polyline_controller
from Controllers import xml_controller
from Controllers import zoom_controller
from Models import dicom_model
from Models import zoom_model
from lib import browse_dialog
from lib import progress_bar
from lib import save_session
from Views import dicom_view
#import Image # PIL (Python Image Library)
import math
import os
import re
#import shutil
import wx

class Controller():
    
    def __init__(self):
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
        self.calib_locked = False
        self.changed = False
        self.pan_image = False # Is the user able to currently pan the image?
        self.toolbar_pan = False
        self.left_down = False # Is the user holding the left mouse button?
        self.polyline_cursor_on = False
        self.debug = False
        self.set_pixels_per_unit = False
        self.coral_controller = None
        self.overlay_controller = None
        self.polyline_controller = None
        self.calibrate_controller = None
        self.save_session = None
        self.background = None
        self.xml = None
        self.plugin_directory = ""
        self.model = dicom_model.Model()
        self.zoom_model = zoom_model.Model()
        self.centerX = 0
        self.centerY = 0
        self.rotations = 0

        self.view = dicom_view.View(self, self.model)
        self.zoom_controller = zoom_controller.Controller(self, self.view, self.model)

        # Check for the XML config file. If it's installed,
        # read the corresponding data. If it's not installed,
        # install it to the user's home directory, setting
        # default values.
        path = os.path.expanduser('~')
        if os.path.exists(r'' + path + os.sep + '.cxvrc.xml'):
            self.xml = xml_controller.Controller(path + os.sep + '.cxvrc.xml')
            self.xml.load_file()
            self.plugin_directory = self.xml.get_plugin_directory()
        else:
            self.xml = xml_controller.Controller(path + os.sep + '.cxvrc.xml')
            self.xml.create_config()

        path = os.path.expanduser('~') + os.sep + "plugins" + os.sep
        
        self.cursor_hand = wx.CursorFromImage(wx.Image(self.view.get_main_dir() + os.sep + 'images' + os.sep + 'cursor_hand_open.gif', wx.BITMAP_TYPE_GIF))
        self.cursor_hand_drag = wx.CursorFromImage(wx.Image(self.view.get_main_dir() + os.sep + 'images' + os.sep + 'cursor_hand_closed.gif', wx.BITMAP_TYPE_GIF))
        image = wx.Image(self.view.get_main_dir() + os.sep + "images" + os.sep + "cursor_cross.png", wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 9)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 9)
        self.cursor_polyline = wx.CursorFromImage(image)

    def on_open(self, event):
        dialog = wx.FileDialog(None, wildcard='CXV files (*.DCM; *.xml; *.cxv)|*.DCM;*.xml;*.cxv|DICOM (*.DCM)|*.DCM|Saved session (*.cxv; *.xml)|*.cxv;*.xml', style=wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            new = True
            if self.model.image_array is not None:  # opening a project on top of another
                self.save_prompt()
                self.close_current()
                new = False
            path = dialog.GetPath()
            savedsesh = False
            if (path[-4:] == '.dcm') or (path[-4:] == '.DCM'):
                self.open_dicom_file(path, new)
            else:
                self.open_saved_session(path, new)
                savedsesh = True
            self.view.aspect_cb.Enable()
            tools = ['Image Overview', 'Image Information', 
                     'Pan Image', 'Zoom In', 'Zoom Out', 
                     'Adjust Target Area', 'Draw Polylines',
                     'Adjust Calibration Region', 'Rotate Image']
            self.enable_tools(tools, True)
            self.enable_tools(['&Save\tCtrl+S'], False)
            self.view.menubar.FindItemById(self.view.menubar_ids['Save As...']).Enable(True)
            self.view.menubar.FindItemById(self.view.menubar_ids['Export']).Enable(True)

            # If the user loads a saved session, we don't want to set these to None!
            if not savedsesh:
                self.coral_controller = None
                self.overlay_controller = None
                self.polyline_controller = None
                self.calibrate_controller = None
            self.centerX, self.centerY = self.model.get_image_shape()

    def open_dicom_file(self, path, new):
        p = path.split(os.sep)
        p = p[:3] + p[-2:]
        p[2] = '...'
        label = 'Loading '
        for each in p:
            label += (each + os.sep)
        label = label[:-1]
        self.pb = progress_bar.ProgressBar('Loading DICOM', label, 7, self.view)
        self.model.image_array = self.model.load_dicom_image(path)
        self.pb.update(label)
        y, x = self.model.get_image_shape()
        self.pb.update(label)
        try: rgba, self.ptr = self.model.allocate_array((y, x, 4))
        except ValueError: rgba, self.ptr = self.model.allocate_array((y, x, 4))
        self.pb.update(label)
        self.model.image_array = self.model.normalize_intensity(self.model.image_array)
        self.pb.update(label)
        self.model.image_array = self.model.invert_grayscale(self.model.image_array)
        self.pb.update(label)
        self.model.image_array = self.model.set_display_data(rgba, self.model.image_array, 1.0)
        self.pb.update(label)
        self.view.init_plot(new)
        self.pb.finish(label)
        self.cleanup()
        self.pb = None

    def open_saved_session(self, path, new):
        if self.view.figure is not None:
            self.view.figure.clear()
        self.save_session = save_session.SaveSession(self, path)
        try:
            self.open_dicom_file(self.save_session.load_file(), new)
        except IOError:
            self.save_session = None
            self.pb.Destroy()
            self.pb = None
            # Image path not found, prompt user to edit XML file with correct path to image
            # TODO: Add section number from manual to this messageBox text
            wx.MessageBox('Image location not found! Please edit the saved session XML file and add the correct image location between the "filename" tags. ' +
                            'For more information on this issue, please consult the CXV manual under section SECTION_NUMBER.', 'Invalid Image Path', wx.OK | wx.ICON_ERROR)
            return
        self.pb = progress_bar.ProgressBar('Loading Session values', "Loading Session values", 7, self.view)
        self.save_session.load(self.pb)
        self.pb.finish("Finished")
        self.pb = None
        self.changed = False
        # Set center correctly for rotations
        if self.rotations == 1 or self.rotations == 3:
            temp = self.centerX
            self.centerX = self.centerY
            self.centerY = temp

    def close_current(self):
        self.model.deallocate_array(self.ptr)
        self.view.figure.delaxes(self.view.axes)
        self.coral_controller = None
        self.overlay_controller = None
        self.polyline_controller = None
        self.save_session = None
        self.changed = False
        self.enable_tools(['Filtered Overlays'], False)

    def on_quit(self, event):
        if self.save_prompt() is not -1: # Cancel button
            wx.Exit()

    def save_prompt(self):
        if self.save_session and self.changed:
            msg = 'The contents of ' + self.save_session.path.split(os.sep)[-1] + \
            ' has changed.\n\n Do you want to save the changes?'
            dialog = wx.MessageDialog(self.view, msg, 'CXV', style=wx.YES_NO|wx.CANCEL)
            choice = dialog.ShowModal()
            if choice==wx.ID_YES:
                self.save_session.write()
            elif choice == wx.ID_CANCEL:
                return -1

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
        self.state_changed(True)

    def resize_image(self, sx=0, sy=0, hide=True, always_hide=False):
        self.resize_mpl_widgets()
        if hide:
            self.view.scroll.Hide()
        self.set_scrollbars(sx, sy)
        self.cache_background()
        if hide and not always_hide:
            self.view.scroll.Show()
        self.cleanup()
        self.update_overview()

    def resize_mpl_widgets(self):
        y, x = self.model.get_image_shape()
        self.view.canvas.resize(x*self.view.aspect, y*self.view.aspect) # canvas gets set in pixels
        self.view.figure.set_size_inches((x*self.view.aspect)/72.0, (y*self.view.aspect)/72.0)  # figure gets set in inches

    def set_scrollbars(self, sx=0, sy=0):
        y, x = self.model.get_image_shape()

        # Setting to (0, 0) first eludes the cropping of the image.
        # If this isn't here, the image will sometimes be cropped and the canvas size
        # will totally change. Weird error... Hopefully there's a better workaround than
        # this.
        self.view.scroll.Scroll(0, 0)
        scroll_unit = self.view.aspect*100.0
        self.su = scroll_unit
        try:
            self.view.scroll.SetScrollbars(scroll_unit, scroll_unit,
                                          (x*self.view.aspect)/scroll_unit,
                                          (y*self.view.aspect)/scroll_unit)
        except ZeroDivisionError:
            # Thrown if the user resizes the entire frame to be too
            # small (less than 0 on either axis). Still may abort
            # the program, however. Minimum size of frame has been
            # set to (100, 100).
            pass
        self.view.scroll.Scroll(sx, sy)
        self.state_changed(True)

    def cache_background(self):
        self.view.canvas.draw() # cache clean slate background
        self.background = self.view.canvas.copy_from_bbox(self.view.axes.bbox)
        self.draw_all()

    def draw_all(self):
        """ Restores the canvas with the cached background,
        then redraws the enabled widgets and finally blits
        the contents of the AGG buffer back to the canvas for
        the user to see.
        """
        self.view.canvas.restore_region(self.background)
        if self.coral_controller:
            self.coral_controller.draw_rect(self.coral, self.coral_locked)
        if self.polyline_controller:
            self.polyline_controller.draw_polylines(self.polyline, self.polyline_locked)
        if self.calibrate_controller:
            self.calibrate_controller.draw_rect(self.calib, False)
            
            # Initiated when the user is calibrating pixels per unit
            if self.calibrate_controller.polyline_controller:
                if self.calibrate_controller.clicks > 0:
                    if self.calibrate_controller.polyline_controller is not None:
                        self.calibrate_controller.polyline_controller.draw_polylines(self.polyline, self.polyline_locked, False)

        self.view.canvas.blit(self.view.axes.bbox)

    def draw_lines(self):
        """ Draws only the rects and polylines on the canvas.
        Does not re-draw the canvas, in order to save time and memory.
        Canvas can be redrawn using self.cache_background() or
        self.draw_all().
        """
        if self.coral_controller:
            self.coral_controller.draw_rect(self.coral, self.coral_locked)
        if self.polyline_controller:
            self.polyline_controller.draw_polylines(self.polyline, self.polyline_locked)
        if self.calibrate_controller:
            self.calibrate_controller.draw_rect(self.calib, False)
        self.view.canvas.Refresh()

    def cleanup(self, event=None):
        try: # ignore first couple calls before canvas instantiation
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
            if not self.polyline:
                self.popup_menu = wx.Menu()
                self.popup_menu.Append(-1, 'Zoom to fit')
    
                # Better to set this event here when we need it because if it's set in
                # the view class, all menu items will fire this event.
                self.view.Bind(wx.EVT_MENU, self.on_popup_item_selected)
                x, y = self.view.scroll.ScreenToClient(wx.GetMousePosition())
                pos = x, y
                self.view.PopupMenu(self.popup_menu, pos)
    
                # Unbind the event, otherwise we get a screen flickering if the user opens
                # multiple popupmenu's without selecting an item. This is caused because
                # there would now be multiple events open and waiting for input. Once input
                # is given, all those events are fired at once, resizing our screen multiple
                # times.
                self.view.Unbind(wx.EVT_MENU)

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

        if not self.pan_image:
            if self.polyline:
                self.polyline_controller.on_mouse_motion(event)
            elif self.coral:
                self.coral_controller.on_mouse_motion(event)
            elif self.calib:
                if self.calibrate_controller is None:
                    self.calib = False
                    return
                self.calibrate_controller.on_mouse_motion(event)

            if not self.zoom:
                self.draw_all()

    def on_mouse_press(self, event):
        if event.button == 1: # Left mouse button
            self.left_down = True
            # Set the prev_x and prev_y to the mouse click position
            try :
                self.previous_x = int(event.xdata)
                self.previous_y = int(event.ydata)
            except TypeError:
                # This is thrown if the user clicks just barely
                # outside of the image bounds (a few pixels at most),
                # when the coordinates show (x, y) in the status bar.
                pass
            if self.pan_image:
                self.view.canvas.SetCursor(self.cursor_hand_drag)
            elif self.zoom:
                self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))
            elif self.polyline_cursor_on:
                self.view.canvas.SetCursor(self.cursor_polyline)
            else:
                self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        elif event.button == 2: # Scroll-wheel button??
            pass
        elif event.button == 3: # Right mouse button
            pass

        if not self.pan_image and not self.zoom:
            if self.polyline:
                self.polyline_controller.on_mouse_press(event)
                self.state_changed(True)
            elif self.coral:
                self.coral_controller.on_mouse_press(event)
            elif self.calib or self.calib_locked:
                self.calibrate_controller.on_mouse_press(event)
            self.draw_all()

        # Update toggle_selector's background.
        self.view.toggle_selector.update_background(event)

    def on_mouse_release(self, event):
        self.left_down = False
        if not self.pan_image and not self.zoom:
            if self.polyline:
                self.polyline_controller.on_mouse_release(event)
            elif self.coral:
                self.coral_slab = self.coral_controller.on_mouse_release(event)
            elif self.calib:
                self.calib_region = self.calibrate_controller.on_mouse_release(event)
            self.draw_all()
        elif self.zoom:
            self.draw_all()

        # Set the cursor accordingly
        if (event.button == 1 or event.button == 3) and self.pan_image:
            self.view.canvas.SetCursor(self.cursor_hand)
        elif (event.button == 1 or event.button == 3) and self.zoom:
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))
        elif (event.button == 1 or event.button == 3) and self.polyline_cursor_on:
            self.view.canvas.SetCursor(self.cursor_polyline)
        else:
            if event.button is not 2:
                self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        # Update toggle_selector's background. Otherwise, next time we try to
        # drag zoom, the objects overlaying the image will disappear during drag
        self.view.toggle_selector.update_background(event)

    def on_key_press(self, event):
        if event.key == ' ' and not self.zoom: # Is the user pressing the SPACE BAR?
            if not self.pan_image:
                self.pan_image = True
                self.view.canvas.SetCursor(self.cursor_hand)
                self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], True)
        elif event.key == 'shift': # Holding SHIFT while setting pixel_per_unit
            if self.calibrate_controller.polyline_controller is not None:
                self.calibrate_controller.polyline_controller.shift_down = True
        elif event.key == 'd': # DEBUG
            if not self.debug:
                self.debug = True
                print "DEBUG Activated..."
            else:
                self.debug = False
                print "DEBUG De-Activated..."

    def on_key_release(self, event):
        if not self.toolbar_pan:
            self.pan_image = False
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], False)
        if self.calibrate_controller is not None:
            if self.calibrate_controller.polyline_controller is not None:
                self.calibrate_controller.polyline_controller.shift_down = False

    def on_figure_leave(self, event):
        self.view.statusbar.SetStatusText("Pixel Position: (x, y)", 0)
        self.view.statusbar.SetStatusText("Pixel Intensity", 1)
 
    def on_scroll(self, event):
        event.Skip()
        self.update_overview()
        self.state_changed(True)

    def on_resize(self, event):
        if event is not None:
            event.Skip()
        if self.ztf:
            try: # ignore first few events before controller instantiation
                y, = self.view.scroll.GetSizeTuple()[-1:]
                iHt, = self.model.get_image_shape()[:-1]
                self.view.aspect = (float(y)/float(iHt))
                self.resize_image(hide=False)
                self.view.aspect_cb.SetValue('Zoom to fit')
                # Update toggle_selector's background. Otherwise, next time we try to
                # drag zoom, the objects overlaying the image will disappear during drag
                self.view.toggle_selector.update_background(event)
                self.view.canvas.Refresh()
            except AttributeError:
                pass
        else:
            self.cleanup()
            self.update_overview()

    def on_aspect(self, event, x=0, y=0, always_hide=False):
        m = self.ztf_patt.match(self.view.aspect_cb.GetValue()) # Zoom to fit
        if m:
            if self.ztf:
                return
            self.ztf = True
            self.on_resize(event)
            self.view.canvas.SetFocus() # Sets focus back to the canvas, otherwise combobox still has keyboard focus
            return
        else: self.ztf = False

        m = self.aspect_patt.match(self.view.aspect_cb.GetValue()) # percent
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

        # Center the screen on the old screen
        if x == 0 and y == 0:
            # Get the previous locations of the scrollbars and set the
            # new scrollbar positions to the same value when the image
            # is resized.
            prev_vertical = self.view.scroll.GetScrollPos(wx.VERTICAL)
            prev_horizontal = self.view.scroll.GetScrollPos(wx.HORIZONTAL)

            self.resize_image(prev_horizontal, prev_vertical, always_hide=always_hide)
        else:
            self.resize_image(x, y, always_hide=always_hide)

        # Update toggle_selector's background. Otherwise, next time we try to
        # drag zoom, the objects overlaying the image will disappear during drag
        self.view.toggle_selector.update_background(event)
        self.view.canvas.Refresh()
        self.view.canvas.SetFocus() # Sets focus back to the canvas, otherwise combobox still has keyboard focus
        self.state_changed(True)

    def on_image_info(self, event):
        try: self.image_info_controller.view.Raise()
        except AttributeError: self.image_info_controller = image_info_controller.Controller(self, self.model)

    def on_coral_menu(self, event):
        """ Menu callback event for drawing coral slab rects """
        if not self.coral:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], True)
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
        self.on_coral(event)

    def on_coral(self, event, zoom_off=True, pan_off=True):
        self.toggle_zoom(zoom_off)
        self.toggle_pan(pan_off)
        self.coral = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Target Area'])
        self.coral_locked = False
        self.polyline = False
        self.calib = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        if not self.coral_controller: # first open
            self.coral_controller = coral_controller.Controller(self.view, self.background)
            self.enable_tools(['Filtered Overlays'], True)
        else:
            try: # remove overlay if already added
                self.view.figure.delaxes(self.view.ov_axes)
                self.overlay_controller.view.Destroy()
                del self.overlay_controller
                self.overlay_controller = None
                self.cache_background()
            except:
                pass
        self.draw_all()
        self.state_changed(True)

    def on_lock_coral(self, event, show=True, alg=True):
        if self.coral_locked: return  # already locked
        self.coral = False
        self.coral_locked = True
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
        self.enable_tools(['Filtered Overlays'], True)
        if alg:
            if not self.overlay_controller:
                self.overlay_controller = overlay_controller.Controller(self.view, self, self.model, self.background, show, self.rotations)
        self.draw_all()
        if alg:
            self.overlay_controller.create_overlays()
        self.cleanup()

    def on_contrast(self, event):
        try: self.contrast_controller.view.Raise()
        except AttributeError: self.contrast_controller = contrast_controller.Controller(self.view, self.model)

    def on_overlay(self, event):
        if not self.coral_locked:
            self.on_lock_coral(event) # have worker thread add and display overlay
        elif not self.overlay_controller.view.IsShown():    # first press
            self.overlay_controller.display()
            self.overlay_controller.view.Show()
        elif self.overlay_controller.view.IsShown():
            self.overlay_controller.view.Raise()

    def on_plugin(self, event):
        """ Filter Plugin submenu """
        pass

    def on_export(self, event):
        """ Exports the DICOM image with all polylines, rectangles,
        and overlays shown in the selected format.
        
        Formats include:
            PNG (*.png)    - Portable Network Graphics
            DXF (*.dxf)    - Autodesk Drawing Exhange Format
            **REMOVED**TIFF (*.tif)   - Tagged Image File Format (Tagged Image File (*.tif)|*.tif|)
        """
        wildcard = 'Portable Network Graphic (*.png)|*.png|Drawing Exchange Format (*.dxf)|*.dxf'
        dialog = wx.FileDialog(self.view, "Export As", style=wx.SAVE|wx.OVERWRITE_PROMPT, wildcard=wildcard)
        dialog.SetFilename(self.model.get_image_name().split('.')[0])
        if dialog.ShowModal()==wx.ID_OK:
            
            # If exporting a DXF, have they set the pixels_per_unit?
            if self.get_file_extension(dialog.GetPath()) == '.dxf':
                if not self.set_pixels_per_unit:
                    wx.MessageBox('Please set the pixels per unit first, using the "Set Calibration Parameters" tool.', 'Pixels Per Unit not set!', wx.OK | wx.ICON_ERROR)
                    return

            pb = progress_bar.ProgressBar('Exporting Image', 'Initiating export', 5, self.view)
            temp = self.view.aspect
            
            # Change to ZTF first to stop memory issues
            self.view.aspect_cb.SetValue('Zoom to fit')
            self.on_aspect(None, 0, 0, always_hide=True) # Set to 100% size
            
            self.view.aspect = 1.00
            self.view.aspect_cb.SetValue(str(int(self.view.aspect*100.0))+'%')
            pb.update('Calculating image size')
            self.on_aspect(None, 0, 0, always_hide=True) # Set to 100% size

            if self.get_file_extension(dialog.GetPath()) == '.dxf': # Save out .dxf file with polylines
                pb.update('Saving DXF file')
                dxf_controller.Controllers().get_model().create_dxf(dialog.GetPath(), self.polyline_controller, self.model, self.calibrate_controller)
            else:
                pb.update('Saving image')
                # Toggle polyline animation off
                lw = self.polyline_controller.get_line_width()
                self.polyline_controller.set_animated(False, lw+3)

                # Save the figure
                self.view.figure.savefig(dialog.GetPath(), dpi=self.view.figure.dpi)

                # Toggle polyline animation on
                self.polyline_controller.set_animated(True, lw)

            self.view.aspect_cb.SetValue(str(int(temp*100.0))+'%')
            pb.update('Finishing up...')
            self.on_aspect(None, 0, 0) # Set back to current size
            self.view.scroll.Show()
            pb.finish('Complete!')

    def get_file_extension(self, file_path):
        """ Returns the file's extension, given the file's path """
        fileName, file_extension = os.path.splitext(file_path)
        return file_extension

    def on_polyline_menu(self, event):
        """ Menu callback event for drawing polylines """
        if not self.polyline:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], True)
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        self.on_polyline(event)

    def on_polyline(self, event, zoom_off=True, pan_off=True):
        self.toggle_zoom(zoom_off)
        self.toggle_pan(pan_off)
        self.polyline = self.view.toolbar.GetToolState(self.view.toolbar_ids['Draw Polylines'])
        self.polyline_locked = False
        self.coral = False
        self.calib = False

        if not self.polyline_cursor_on:
            self.view.canvas.SetCursor(self.cursor_polyline)
            self.polyline_cursor_on = True
        else:
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.polyline_cursor_on = False

        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        if not self.polyline_controller:
            self.polyline_controller = polyline_controller.Controller(self, self.view, self.background)
        self.draw_all()
        self.state_changed(True)

    def on_lock_polyline(self, event):
        self.polyline = False
        self.polyline_locked = True
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        self.draw_all()

    def on_calibrate_menu(self, event):
        """ Menu callback event for drawing calibration rects """
        if not self.calib:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], True)
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        self.on_calibrate(event)

    def on_calibrate(self, event, zoom_off=True, pan_off=True):
        """ Enables or disables the 'Adjust Calibration Region' """
        self.toggle_zoom(zoom_off)
        self.toggle_pan(pan_off)
        if self.calib:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
            self.calib = False
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], True)
            self.calib = True
        self.coral = False
        self.polyline = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
        if not self.calibrate_controller:
            self.calibrate_controller = calibrate_controller.Controller(self.view, self.background)
            self.enable_tools(['Set Calibration Parameters'], True)
        self.draw_all()
        self.state_changed(True)

    def on_density_params(self, event, show=True, zoom_off=True, pan_off=True):
        """ Opens the calibration parameters dialog """
        self.toggle_zoom(zoom_off)
        self.toggle_pan(pan_off)
        self.calib = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
        if show:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Set Calibration Parameters'], True)
            self.calibrate_controller.on_density_params(event)
        self.draw_all()
        self.state_changed(True)

    def on_save(self, event):
        if not self.save_session:
            self.on_save_as(event)
        else:
            self.save_session.write()
            self.state_changed(False)

    def on_save_as(self, event):
        """ Shows a save as dialog where the user choose to save the file
        on their system with a specific filename and extension.
        """
        dialog = wx.FileDialog(self.view, "Save As", style=wx.SAVE|wx.OVERWRITE_PROMPT, wildcard='CXV Session File (*.cxv)|*.cxv|XML Document (*.xml)|*.xml')

        dialog.SetFilename(self.model.get_image_name().split('.')[0])

        if dialog.ShowModal() == wx.ID_OK:
            # Is the user saving a CXV Session file or XML file?
            path = dialog.GetPath()
            if self.get_file_extension(path) == '.cxv':
                dialog.SetFilename(self.model.get_image_name().split('.')[0]+'.cxv')
            else:
                dialog.SetFilename(self.model.get_image_name().split('.')[0]+'.xml')

            self.save_session = save_session.SaveSession(self, path)
            self.save_session.write()
            self.state_changed(False)
        else:
            self.state_changed(True)

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
        li = [" ".join(words[i:i+span]) for i in range(0, len(words), span)]
        description = '\n'.join(li)

        info = wx.AboutDialogInfo()
        info.SetName(plugin.name)
        info.SetVersion(plugin.version)
        info.SetDescription(description)
        info.SetWebSite(plugin.website)
        info.AddDeveloper(plugin.author)

        wx.AboutBox(info)

    def on_pan_image_menu(self, event):
        """ Menu callback event for panning """
        if not self.pan_image:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], True)
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], False)
        self.on_pan_image(event)

    def on_pan_image(self, event):
        if self.toolbar_pan:
            self.toolbar_pan = False
        else:
            self.toolbar_pan = True

        if self.view.toolbar.GetToolState(self.view.toolbar_ids['Pan Image']):
            self.pan_image = True

            # Un-toggle toolbar items that may currently be toggled
            self.toggle_target_area()
            self.toggle_calibration_region()
            self.toggle_polyline()

            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Zoom In'], False)
            self.zoom = False
            self.view.toggle_selector.set_active(False)
            self.view.canvas.SetCursor(self.cursor_hand)
        else:
            self.pan_image = False
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

    def on_help(self, event):
        print 'Help'
        pass

    def on_about(self, event):
        print 'About'
        pass

    def rotate(self):
        # Swap the center's X and Y coordinates to correctly rotate image multiple times
        temp = self.centerX
        self.centerX = self.centerY
        self.centerY = temp

        cx = self.centerX / 2
        cy = self.centerY / 2

        self.model.rotate_image(self.model.get_image())

        # Redraw the canvas to show the rotated image
        self.view.axes.cla() # Clear the axes
        self.view.init_plot(False) # Redraw

        # Rotate polylines accordingly
        if self.polyline_controller is not None:
            self.polyline_controller.rotate_lines(cx, cy)
        if self.coral_controller is not None:
            self.coral_controller.rotate_lines(cx, cy)
            self.coral_controller.refresh_area()
        if self.calibrate_controller is not None:
            self.calibrate_controller.rotate_lines(cx, cy)
            self.calibrate_controller.refresh_area()
        
        self.cache_background()

    def on_rotate(self, event, rot=None):
        """ Rotates the image by 90 degrees (counter-clockwise) """
        if self.coral_controller is not None:
            self.on_coral(event)

        if rot is None:
            if self.rotations <= 2:
                self.rotations += 1
            else:
                self.rotations = 0
            self.rotate()
        else:
            for i in xrange(rot):
                self.rotate()

    def toggle_target_area(self):
        """ Toggles off the target area button in the toolbar if it's enabled. """

        # Un-toggle toolbar items that may currently be toggled
        coral_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Target Area'])

        if coral_on: # Turn off coral region
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
            self.on_coral(None, zoom_off=True, pan_off=False)

    def toggle_calibration_region(self):
        """ Toggles off the calibration region button in the toolbar if it's enabled. """
        calib_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Calibration Region'])

        if calib_on: # Turn off calibration region
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
            self.on_calibrate(None, zoom_off=True, pan_off=False)

    def toggle_polyline(self):
        """ Toggles off the polyline button in the toolbar if it's enabled. """
        polyline_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Draw Polylines'])

        if polyline_on: # Turn of polylines
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
            self.on_polyline(None, zoom_off=True, pan_off=False)
    
    def toggle_zoom(self, zoom_off):
        """ Toggles the zoom button in the toolbar, given the
        zoom_off parameter.
        """
        if zoom_off:
            self.zoom = False
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Zoom In'], False)
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.toggle_selector.set_active(False)
        else:
            self.zoom = True

    def toggle_pan(self, pan_off):
        """ Toggles the pan image button in the toolbar, given the
        pan_off parameter.
        """
        if pan_off:
            self.pan_image = False
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], False)
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        else:
            self.pan_image = True

    def state_changed(self, changed):
        """ This method is called when the user changes something and the
        current version differs from the previously saved version.
        
        @var changed - Does the program differ from the previously saved session?
        """
        if changed:
            self.enable_tools(['&Save\tCtrl+S'], True)
        else:
            self.enable_tools(['&Save\tCtrl+S'], False)
        self.changed = changed
