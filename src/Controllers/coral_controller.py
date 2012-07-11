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
from Models import rectangle_model
import wx

class Controller():
    
    def __init__(self, dicom_view, background):
        self.dicom_view = dicom_view
        self.model = rectangle_model.Model(self.dicom_view, background, 200, 200, 600, 600)
        self.dicom_view.controller.coral_slab = [self.model.sx, self.model.sy, self.model.dx, self.model.dy]

    def on_mouse_motion(self, event):
        self.model.on_mouse_motion(event)

    def on_mouse_press(self, event):
        if event.button == 1: # Left click
            self.model.on_mouse_press(event)
        elif event.button == 2: # Scroll-wheel click
            pass
        elif event.button == 3: # Right click
            x, y, w, h = self.model.get_rect_pos()
            if self.model.is_mouse_in_rect(event):
                self.create_popup_menu()
                return

    def on_mouse_release(self, event):
        # Unbind the other event here because it will help stop unhandled mouse events
        self.dicom_view.Unbind(wx.EVT_MOUSE_CAPTURE_LOST)
        return self.model.on_mouse_release(event)

    def on_pick(self, event):
        self.model.on_pick(event)

    def adjust_rect(self, event):
        self.model.adjust_rect(event)

    def check_bounds(self):
        self.check_bounds()

    def draw_rect(self, adjustable, locked):
        self.model.draw_rect(adjustable, locked, 'y')

    def create_popup_menu(self):
        self.menu = wx.Menu()
        if self.dicom_view.controller.coral_locked:
            self.add_option(self.menu, 'Unlock Coral Slab', self.on_popup_item_selected)
        for each in self.popup_line_data():
            self.add_option(self.menu, *each)
        try: self.dicom_view.PopupMenu(self.menu)
        except: pass    # Avoid C++ assertion error
        self.menu.Destroy()

    def add_option(self, menu, label, handler):
        option = menu.Append(-1, label)
        self.dicom_view.Bind(wx.EVT_MENU, handler, option)

    def popup_line_data(self):
        return [('Lock Coral Slab', self.on_popup_item_selected),
                ('Delete Coral Slab', self.delete_coral_slab)]

    def delete_coral_slab(self, event):
        self.model = None
        del self.model
        self.dicom_view.controller.coral = False
        self.dicom_view.controller.coral_controller = None
        self.dicom_view.controller.enable_tools(['Lock Coral Slab'], False)
        self.dicom_view.controller.enable_tools(['Filtered Overlays'], False)
        self.dicom_view.toolbar.ToggleTool(self.dicom_view.toolbar_ids['Adjust Coral Slab'], False)
        del self

    def on_popup_item_selected(self, event):
        """ Fired when the user selects a popup item on the rectangle model.
        NOTE: If more events are added for different rectangle models, those
        cases will need to be added here. Currently, it will fire all events
        added.
        """
        if not self.dicom_view.controller.coral_locked:
            self.dicom_view.controller.on_lock_coral(event, True)
        else:
            self.dicom_view.controller.on_coral(event)