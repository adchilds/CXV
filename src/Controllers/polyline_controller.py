#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Models import polyline_model as pl
import numpy as np
import math
import os
import wx

class Controller():

    def __init__(self, dicom_controller, dicom_view, background, calib=False):
        self.dicom_controller = dicom_controller
        self.dicom_view = dicom_view
        self.canvas = self.dicom_view.canvas
        self.axes = self.dicom_view.axes
        self.background = background
        self.drag_v = False
        self.drag_pl = False
        self.prev_event = None
        self.tmp_line = None
        self.right_line = None
        self.left_line = None
        self.picked = None
        self.connect = False
        self.shift_down = False
        self.polylines = []
        self.curr_pl = None
        self.color_map = {'Red' : '#FF0000',
                          'Green' : '#00FF00',
                          'Blue' : '#0000FF',
                          'Yellow' : '#FFFF00',
                          'Purple' : '#FF00FF',
                          'Pink' : '#FF99FF',
                          'Orange' : '#FF9900',
                          'White' : '#FFFFFF',
                          'Black' : '#000000'}

        # Polyline cursor
        image = wx.Image(self.dicom_view.get_main_dir() + os.sep + "images" + os.sep + "cursor_cross.png", wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 9)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 9)
        self.cursor = wx.CursorFromImage(image)

        # Polyline cursor focus
        image = wx.Image(self.dicom_view.get_main_dir() + os.sep + "images" + os.sep + "cursor_cross_dot.png", wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 9)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 9)
        self.cursor_dot = wx.CursorFromImage(image)

        # Setting pixels per unit cursor
        image = wx.Image(self.dicom_view.get_main_dir() + os.sep + "images" + os.sep + "cursor_ppu.png", wx.BITMAP_TYPE_PNG)
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 10) 
        image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 10)
        self.cursor_ppu = wx.CursorFromImage(image)
 
        self.calib = calib

    def on_mouse_motion(self, event):
        if len(self.polylines) == 0: return
        if event.inaxes == self.dicom_view.ov_axes:
            event.xdata += self.dicom_controller.coral_slab[0]
            event.ydata += self.dicom_controller.coral_slab[1]
        if self.drag_v:
            self.dicom_view.canvas.SetCursor(self.cursor)
            self.drag_vertex(event)
        elif self.drag_pl:
            self.dicom_view.canvas.SetCursor(self.cursor)
            self.drag_polyline(event)
        elif self.connect:
            x, = self.curr_pl.verticies[-1].get_xdata()
            y, = self.curr_pl.verticies[-1].get_ydata()

            # Is the user's mouse moving horizontal or vertical?
            try:
                if math.fabs(x - event.xdata) > math.fabs(y - event.ydata):
                    moving_horizontal = True
                else:
                    moving_horizontal = False
            except TypeError:
                moving_horizontal = True

            if self.calib:
                # Set the cursor
                self.dicom_view.canvas.SetCursor(self.cursor_ppu)

                # If setting pixels_per_unit, draw the line like: |---------|
                # So the user can see the start and end point clearly
                
                if self.shift_down:
                    if moving_horizontal:
                        self.left_line, = self.axes.plot([x, x], [y+10, y-10],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.tmp_line, = self.axes.plot([x, event.xdata], [y, y],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.right_line, = self.axes.plot([event.xdata, event.xdata], [y+10, y-10],
                                                          c='#00FF00', linestyle='-',
                                                          zorder=1, animated=True)
                    else:
                        self.left_line, = self.axes.plot([x+10, x-10], [y, y],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.tmp_line, = self.axes.plot([x, x], [y, event.ydata],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.right_line, = self.axes.plot([x+10, x-10], [event.ydata, event.ydata],
                                                          c='#00FF00', linestyle='-',
                                                          zorder=1, animated=True)
                else:
                    if moving_horizontal:
                        self.left_line, = self.axes.plot([x, x], [y+10, y-10],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.right_line, = self.axes.plot([event.xdata, event.xdata], [event.ydata+10, event.ydata-10],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                    else:
                        self.left_line, = self.axes.plot([x+10, x-10], [y, y],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                        self.right_line, = self.axes.plot([event.xdata+10, event.xdata-10], [event.ydata, event.ydata],
                                                        c='#00FF00', linestyle='-',
                                                        zorder=1, animated=True)
                    self.tmp_line, = self.axes.plot([x, event.xdata], [y, event.ydata],
                                                    c='#00FF00', linestyle='-',
                                                    zorder=1, animated=True)
            else:
                self.tmp_line, = self.axes.plot([x, event.xdata], [y, event.ydata],
                                                c='#00FF00', linestyle='-',
                                                zorder=1, animated=True)
        elif self.over_polyline(event):
            if self.picked.contains(event)[0]:
                if not self.dicom_controller.zoom and not self.dicom_controller.pan_image:
                    self.dicom_view.canvas.SetCursor(self.cursor_dot)
        else:
            self.dicom_view.canvas.SetCursor(self.cursor)
        self.prev_event = event
        try: self.curr_pl.set_label(self.polylines.index(self.curr_pl))
        except: pass

    def on_mouse_press(self, event, vert=True):
        if event.inaxes == self.dicom_view.ov_axes:
            event.xdata += self.dicom_controller.coral_slab[0]
            event.ydata += self.dicom_controller.coral_slab[1]
        if event.button == 1:
            self.on_left_click(event, vert)
        elif event.button == 3:
            self.on_right_click(event, vert)

    def on_mouse_release(self, event):
        self.drag_v = False
        self.drag_pl = False

    def on_key_press(self, event, shift=False):
        self.shift_down = shift

    def on_key_release(self, event):
        self.shift_down = False

    def on_left_click(self, event, vert=True):
        if self.on_pick(event, vert):
            if vert:
                self.dicom_view.canvas.SetCursor(self.cursor)
            return
        if self.connect:
            self.append_tmp_line()
        else:
            self.curr_pl = pl.Polyline(self, self.axes)
            self.polylines.append(self.curr_pl)
            self.connect = True
            self.dicom_controller.changed = True
        self.curr_pl.add_vertex(event.xdata, event.ydata)

    def on_right_click(self, event, vert=True):
        if self.connect:
            self.tmp_line = None
            self.connect = False
            self.curr_pl.color = '#FF0000'
            self.curr_pl.set_colors()
            self.validate()
        elif self.on_pick(event, vert):
            self.dicom_controller.draw_all()
            if self.picked.contains(event)[0]:
                self.mpl_event = event
                self.create_popup_menu(self.curr_pl.is_line(self.picked))
        else:
            self.dicom_controller.on_polyline_menu(None) # Lock the polylines

    def on_pick(self, event, vert=True):
        self.picked = None
        for polyline in self.polylines:
            for line in polyline.lines:
                if line.contains(event)[0]:
                    self.picked = line
                    self.curr_pl = polyline
                    self.drag_pl = True
            if vert:
                for vertex in polyline.verticies:
                    if vertex.contains(event)[0]:
                        self.picked = vertex
                        self.curr_pl = polyline
                        self.drag_v = True
        if not self.picked: return False
        else: return True

    def rotate_lines(self, cx, cy, deg=-90):
        # Convert from degrees to radians
        theta = math.radians(deg)

        for pl in self.polylines:
            self.curr_pl = pl
            v = 0
            for line in pl.lines:
                # Get the vertices of the line
                px, ox = line.get_xdata()
                py, oy = line.get_ydata()

                M = self.rotateAndTranslate(theta, cx, cy, px, py)

                M2 = self.rotateAndTranslate(theta, cx, cy, ox, oy)

                # Set the line to it's new coordinate
                self.curr_pl.set_line(line,
                                      [float(M[0][0]), float(M2[0][0])],
                                      [float(M[1][0]), float(M2[1][0])])

                self.curr_pl.set_vertex(self.curr_pl.get_vertex(v), float(M[0][0]), float(M[1][0]))
                self.curr_pl.set_vertex(self.curr_pl.get_vertex(v+1), float(M2[0][0]), float(M2[1][0]))
                
                # Reset label for line
                if v == 0:
                    x1 = float(M[0][0])
                    y1 = float(M[1][0])
                    x2 = float(M2[0][0])
                    y2 = float(M2[1][0])
                    self.curr_pl.set_label_pos(x1, y1, x2, y2)
                v += 1

    def rotateAndTranslate(self, theta, originX, originY, x=0, y=0):
        """
        Applies the rotation transformation by 'theta'
        degrees to the provided points around the specified
        point (originX, originY). Translates to and from
        the origin (originX, originY) before and after rotation.
        """
        # Un-translation
        A = np.matrix([[1, 0, originX],
                       [0, 1, originY],
                       [0, 0, 1]])
        
        # Rotation
        B = np.matrix([[math.cos(theta), -math.sin(theta), 0],
                       [math.sin(theta), math.cos(theta), 0],
                       [0, 0, 1]])
        
        # Translation
        C = np.matrix([[1, 0, -originY], # swap the Y and X here because image dimensions changed
                       [0, 1, -originX],
                       [0, 0, 1]])
        
        # Vertex position
        D = np.matrix([[x],
                       [y],
                       [1]])

        return (A * B * C * D)

    def over_polyline(self, event):
        self.picked = None
        for polyline in self.polylines:
            for line in polyline.lines:
                if line.contains(event)[0]:
                    self.picked = line
            for vertex in polyline.verticies:
                if vertex.contains(event)[0]:
                    self.picked = vertex
        if not self.picked: return False
        else: return True

    def delete_polyline(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        self.polylines.remove(self.curr_pl)
        for i in range(len(self.polylines)):
            self.polylines[i].set_label(i)

    def add_vertex(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        line_index = self.curr_pl.get_line_index(self.picked)
        new_line = self.curr_pl.insert_line(line_index+1, [0,0], [0,0])
        new_vertex = self.curr_pl.insert_vertex(line_index+1,
                                                self.mpl_event.xdata,
                                                self.mpl_event.ydata)
        self.curr_pl.set_line(self.picked, 
                              [self.picked.get_xdata()[0], self.mpl_event.xdata],
                              [self.picked.get_ydata()[0], self.mpl_event.ydata])
        v = self.curr_pl.get_vertex(line_index+2)
        self.curr_pl.set_line(new_line,
                              [self.mpl_event.xdata, v.get_xdata()[0]],
                              [self.mpl_event.ydata, v.get_ydata()[0]])
        self.picked = new_vertex
        self.curr_pl.set_colors()

    def delete_vertex(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        if self.curr_pl.is_first(self.picked):
            self.curr_pl.remove_vertex(0)
            self.curr_pl.remove_line(0)
        elif self.curr_pl.is_last(self.picked):
            self.curr_pl.verticies.pop()
            self.curr_pl.lines.pop()
        else:
            vertex_index = self.curr_pl.get_vertex_index(self.picked)
            self.curr_pl.remove_vertex(vertex_index)
            self.curr_pl.remove_line(vertex_index-1)
            l = self.curr_pl.get_line(vertex_index-1)
            v = self.curr_pl.get_vertex(vertex_index-1)
            self.curr_pl.set_line(l,
                                  [v.get_xdata()[0], l.get_xdata()[1]], 
                                  [v.get_ydata()[0], l.get_ydata()[1]])
        self.validate()

    def set_color(self, event):
        self.drag_v = False
        self.drag_pl = False
        color = self.menu.FindItemById(event.GetId()).GetItemLabel()
        self.curr_pl.color = self.color_map[color]
        self.curr_pl.set_colors()

    def append_tmp_line(self):
        self.curr_pl.add_line(self.tmp_line.get_xdata(), self.tmp_line.get_ydata())
        self.tmp_line = None

    def validate(self):
        if self.curr_pl.is_alone():
            self.polylines.remove(self.curr_pl)
            self.curr_pl = None

    def drag_vertex(self, event):
        self.dicom_controller.changed = True
        i = self.curr_pl.get_vertex_index(self.picked)
        self.curr_pl.set_vertex(self.picked, event.xdata, event.ydata)
        if not self.curr_pl.is_first(self.picked):
            line = self.curr_pl.get_line(i-1)
            self.curr_pl.set_line(line,
                                  [line.get_xdata()[0], event.xdata],
                                  [line.get_ydata()[0], event.ydata])
        if not self.curr_pl.is_last(self.picked):
            line = self.curr_pl.get_line(i)
            self.curr_pl.set_line(line,
                                  [event.xdata, line.get_xdata()[1]],
                                  [event.ydata, line.get_ydata()[1]])

    def drag_polyline(self, event):
        self.dicom_controller.changed = True

        # TODO: TypeError thrown here when the user's mouse
        # goes outside of the canvas while dragging polyline
        #
        # Unsure how to write the try/except for this, however.
        x_offset = event.xdata - self.prev_event.xdata
        y_offset = event.ydata - self.prev_event.ydata

        try:
            for line in self.curr_pl.lines:
                x1, x2 = line.get_xdata()
                y1, y2 = line.get_ydata()
                x1 += x_offset
                x2 += x_offset
                y1 += y_offset
                y2 += y_offset
                self.curr_pl.set_line(line,
                                      [x1, x2],
                                      [y1, y2])
            for vertex in self.curr_pl.verticies:
                x, = vertex.get_xdata()
                y, = vertex.get_ydata()
                x += x_offset
                y += y_offset
                self.curr_pl.set_vertex(vertex, x, y)
        except ValueError:
            pass

    def draw_polylines(self, adjustable, locked, show_label=True):
        if self.tmp_line: self.axes.draw_artist(self.tmp_line)
        if self.right_line:
            self.axes.draw_artist(self.right_line)
            self.axes.draw_artist(self.left_line)
        for polyline in self.polylines:
            for line in polyline.lines:
                self.axes.draw_artist(line)
            if adjustable:
                for vertex in polyline.verticies:
                    self.axes.draw_artist(vertex)
            if show_label:
                self.axes.draw_artist(polyline.label)

    def create_popup_menu(self, line):
        if not self.picked: return
        self.menu = wx.Menu()
        if line:
            for each in self.popup_line_data():
                self.add_option(self.menu, *each)
        else:
            for each in self.popup_vertex_data():
                self.add_option(self.menu, *each)
        color_menu = wx.Menu()
        for each in self.popup_color_data():
            self.add_option(color_menu, *each)
        self.menu.AppendMenu(-1, 'Color', color_menu)
        try: self.dicom_view.PopupMenu(self.menu)
        except: pass    # avoid C++ assertion error
        self.menu.Destroy()

    def add_option(self, menu, label, handler):
        option = menu.Append(-1, label)
        self.dicom_view.Bind(wx.EVT_MENU, handler, option)

    def popup_line_data(self):
        return [('Add Vertex Here', self.add_vertex),
                ('Delete Polyline ' + self.curr_pl.get_label(), self.delete_polyline)
#                ('Duplicate Polyline', self.on_duplicate)
                ]

    def popup_vertex_data(self):
        return [('Delete Vertex', self.delete_vertex),
                ('Delete Polyline ' + self.curr_pl.get_label(), self.delete_polyline)
#                ('Duplicate Polyline', self.on_duplicate)
                ]

    def popup_color_data(self):
        return [
                ('Red', self.set_color),
                ('Green', self.set_color),
                ('Blue', self.set_color),
                ('Yellow', self.set_color),
                ('Purple', self.set_color),
                ('Pink', self.set_color),
                ('Orange', self.set_color),
                ('White', self.set_color),
                ('Black', self.set_color)
                ]

    def get_line_width(self):
        """ Returns the current width of the polylines. We only
        need to check the first one, since they should all be the
        same.
        """
        for polyline in self.polylines:
            for line in polyline.lines:
                return line.get_linewidth()
        return None # if no lines exist

    def set_animated(self, anim, line_width):
        """ Toggles the animation of lines on or off. Used when saving
        the figure. If lines are animated, they do not show in the saved
        image.
        
        @var anim - boolean value indicating whether or not the lines should be animated
        @var line_width - the line width the change the polylines to (bigger is better for saving)
        """
        for polyline in self.polylines:
            for line in polyline.lines:
                line.set_animated(anim)
                line.set_linewidth(line_width)

    def on_duplicate(self, event):
        """ Creates an exact copy of another polyline and places it
        a few pixels away from the other one. """
        print 'Duplicate Polyline'