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
from Controllers import polyline_controller
from Models import zoom_model
import math
import wx

class Controller():
    """ The zoom_controller, hence it's name, controls zooming 
    within the CXV program. """

    def __init__(self, dicom_controller, dicom_view, dicom_model):
        self.dicom_controller = dicom_controller
        self.dicom_model = dicom_model
        self.model = zoom_model.Model()
        self.view = dicom_view

    def on_drag_zoom(self, drag_coords=None):
        """ Invoked when the user has the zoom button in the toolbar
        toggled and then drags a rectangular area and releases the mouse.
        First, calculates the correct amount to zoom in where the entire selected area
        fills as most of the current window size without cutting any part of the
        selected area out. Second, calculates where the scrollbars need to be positioned
        in order to show the selected area in the ScrolledWindow.
        
        @var drag_coords - The rect that the user has selected
        """
        x1, y1, x2, y2 = drag_coords # Selected area dimensions
        rect_width, rect_height = (math.fabs(x2 - x1), math.fabs(y2 - y1)) # Rect dimensions
        scroll_width, scroll_height = self.view.scroll.GetSizeTuple() # ScrolledWindow dimensions

        # Get the center point of the dragged area
        dX, dY = self.model.center_of_rect(x1, y1, x2, y2)

        # Ratio of the selected area to the ScrolledWindow
        # Calculates how far we're able to zoom in
        ratio = self.model.rect_ratio(rect_width, rect_height, scroll_width, scroll_height)

        # Zoom the image accordingly
        if ratio > 1.20:
            self.view.aspect = 1.20
            self.view.aspect_cb.SetValue('120%')
        elif ratio < 0.1:
            self.view.aspect = 0.1
            self.view.aspect_cb.SetValue('10%')
        else:
            self.view.aspect = ratio
            self.view.aspect_cb.SetValue(str(int(ratio*100.0))+'%')

        # Resize behind the scenes so we can calculate scrollbar positions correctly
        self.dicom_controller.resize_mpl_widgets()

        # Get the center point of the view
        c = self.model.get_viewable_rect(self.view)
        vX, vY = self.model.center_of_rect(c[0], c[1], c[2], c[3])

        # Calculate how many scroll units they're apart by
        x1 = math.fabs(vX - dX) / 100
        y1 = math.fabs(vY - dY) / 100

        # Round these values and cast them as integers
        x1 = int(round(x1))
        y1 = int(round(y1))

        # Resize and scroll the image
        self.dicom_controller.on_aspect(None, x1, y1)

    def on_zoom(self, click, release):
        """ Invoked when the user is using the RectangleSelector class.
        In other words, the user is dragging a rectangular area with their
        mouse, while the zoom-in button is toggled.
        """
        x1, y1 = click.xdata, click.ydata
        x2, y2 = release.xdata, release.ydata
        self.dicom_controller.ztf = False
        self.on_drag_zoom([x1, y1, x2, y2])
        self.dicom_controller.cache_background()

    def on_zoom_in_menu(self, event):
        """ Menu callback event zooming """
        if not self.dicom_controller.zoom:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Zoom In'], True)
        else:
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Zoom In'], False)
        self.on_zoom_in(event)

    def on_zoom_in(self, event):
        """ Invoked when the user presses the zoom in button
        in the toolbar or menubar.
        """
        self.dicom_controller.zoom = self.view.toolbar.GetToolState(self.view.toolbar_ids['Zoom In'])

        if self.dicom_controller.zoom: # Zoom ON
            # Un-toggle toolbar items that may currently be toggled
            coral_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Target Area'])
            calib_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Adjust Calibration Region'])
            polyline_on = self.view.toolbar.GetToolState(self.view.toolbar_ids['Draw Polylines'])

            if coral_on: # Turn off coral region
                self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Target Area'], False)
                self.dicom_controller.on_coral(None, zoom_off=False, pan_off=True)
            if calib_on: # Turn off calibration region
                self.view.toolbar.ToggleTool(self.view.toolbar_ids['Adjust Calibration Region'], False)
                self.dicom_controller.on_calibrate(None, zoom_off=False, pan_off=True)
            if polyline_on: # Turn of polylines
                self.view.toolbar.ToggleTool(self.view.toolbar_ids['Draw Polylines'], False)
                self.dicom_controller.on_polyline(None, zoom_off=False, pan_off=True)
            self.view.toolbar.ToggleTool(self.view.toolbar_ids['Pan Image'], False)
            self.dicom_controller.pan_image = False

            # Change the cursor
            #cur = wx.CursorFromImage(wx.Image("images/zoom_in.png", wx.BITMAP_TYPE_PNG))
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))

            # Set the rectangle selector to active
            self.view.toggle_selector.set_active(True)

            # Update the toggle_selector, otherwise we get a nasty opaque
            # box the first time that the user attempts to drag and zoom
            self.view.toggle_selector.update()
            self.view.toggle_selector.update_background(event)

            # Need to redraw the lines when the zoom-in button is pressed
            # because otherwise, newly created rects or polylines will become
            # invisible.
            self.dicom_controller.draw_all()
        else: # Zoom OFF
            self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.view.toggle_selector.set_active(False)

    def on_zoom_out(self, event):
        """ Invoked when the user presses the zoom out button
        in the toolbar or menubar.
        """
        self.dicom_controller.zoom = False
        self.dicom_controller.ztf = False
        self.view.toolbar.ToggleTool(self.view.toolbar_ids['Zoom In'], False)
        self.view.canvas.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.view.toggle_selector.set_active(False)
        self.view.aspect -= 0.1
        if self.view.aspect < 0.1:
            self.view.aspect = 0.1
            self.view.aspect_cb.SetValue('10%')
        else:
            self.view.aspect_cb.SetValue(str(int(self.view.aspect*100.0))+'%')
        self.dicom_controller.on_aspect(None)
        # Update toggle_selector's background. Otherwise, next time we try to
        # drag zoom, the objects overlaying the image will disappear during drag
        self.view.toggle_selector.update_background(event)
        self.view.canvas.SetFocus() # Sets focus back to the canvas, otherwise combobox has keyboard focus